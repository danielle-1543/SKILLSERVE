"""Catalog editing and bounded, validated worker specialty selections."""
import json
import unicodedata
from django import forms
from django.utils.text import slugify
from django.db import transaction
from accounts.models import SkillCategory, SpecialtyTag, WorkerSpecialty


def normalized(value):
    return ' '.join(unicodedata.normalize('NFKC', value).split())


class CategoryForm(forms.ModelForm):
    specialties = forms.CharField(required=False, label='Suggested services (optional, legacy)', widget=forms.Textarea(attrs={'rows':6, 'placeholder':'Leak repair\nPipe installation\nDrain cleaning'}), help_text='Optional reference suggestions. Workers write their own Services Offered.')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound and self.instance.pk:
            self.initial['specialties'] = '\n'.join(self.instance.tags.values_list('name', flat=True))

    def clean_specialties(self):
        names = [normalized(line) for line in self.cleaned_data['specialties'].splitlines() if normalized(line)]
        if len(names) > 100:
            raise forms.ValidationError('Enter up to 100 suggestions, one per line.')
        keys = [name.casefold() for name in names]
        if len(keys) != len(set(keys)):
            raise forms.ValidationError('Remove duplicate specialty names.')
        if any(len(name) > 80 for name in names):
            raise forms.ValidationError('Each specialty must be 80 characters or less.')
        if self.instance.pk:
            for tag in self.instance.tags.all():
                if tag.name.casefold() not in keys and tag.worker_specialties.exists():
                    raise forms.ValidationError(f'"{tag.name}" is used by workers and cannot be removed. Use its Edit link to rename it.')
        return names
    class Meta:
        model = SkillCategory
        fields = ['name']
        labels = {'name': 'Type of Service'}

    def clean_name(self):
        value = normalized(self.cleaned_data['name'])
        if value.casefold() in {'other', 'others'}:
            raise forms.ValidationError('Use a specific category name, not Others.')
        return value

    def save(self, commit=True):
        category = super().save(commit=False)
        if not category.slug:
            base = slugify(category.name)[:105] or 'skill-category'
            candidate, suffix = base, 2
            while SkillCategory.objects.exclude(pk=category.pk).filter(slug=candidate).exists():
                candidate = f'{base}-{suffix}'
                suffix += 1
            category.slug = candidate
        if commit:
            with transaction.atomic():
                category.save()
                names = self.cleaned_data['specialties']
                wanted = {name.casefold(): name for name in names}
                existing = {tag.name.casefold(): tag for tag in category.tags.all()}
                for key, tag in existing.items():
                    if key not in wanted:
                        tag.delete()
                    elif tag.name != wanted[key]:
                        tag.name = wanted[key]
                        tag.save(update_fields=['name'])
                for key, name in wanted.items():
                    if key not in existing:
                        SpecialtyTag.objects.create(category=category, name=name)
        return category


class TagForm(forms.ModelForm):
    class Meta:
        model = SpecialtyTag
        fields = ['category', 'name']

    def clean_name(self):
        return normalized(self.cleaned_data['name'])

    def clean_category(self):
        category = self.cleaned_data['category']
        if self.instance.pk and self.instance.worker_specialties.exists() and category.pk != self.instance.category_id:
            raise forms.ValidationError('A used tag cannot be moved to a different category.')
        return category


class WorkerSkillsForm(forms.Form):
    specialties = forms.CharField(widget=forms.HiddenInput, max_length=15000)

    def __init__(self, *args, profile, **kwargs):
        self.profile = profile
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.initial['specialties'] = json.dumps([
                {'category': row.category_id, 'tag': row.tag_id, 'custom': row.custom_text}
                for row in profile.specialties.all()
            ])

    def clean_specialties(self):
        try:
            rows = json.loads(self.cleaned_data['specialties'])
        except (ValueError, TypeError):
            raise forms.ValidationError('Select your skills again.')
        if not isinstance(rows, list) or not 1 <= len(rows) <= 30:
            raise forms.ValidationError('Add between 1 and 30 specialties.')
        result, seen = [], set()
        categories = {c.pk:c for c in SkillCategory.objects.all()}
        tags = {t.pk:t for t in SpecialtyTag.objects.all()}
        for row in rows:
            if not isinstance(row, dict) or (type(row.get('category')) is not int or row['category'] < 1) or (row.get('tag') is not None and (type(row['tag']) is not int or row['tag'] < 1)):
                raise forms.ValidationError('Invalid specialty selection.')
            category = categories.get(row['category'])
            tag_id = row.get('tag')
            raw_custom = row.get('custom', '')
            if not isinstance(raw_custom, str):
                raise forms.ValidationError('Enter a valid specialty name.')
            custom = normalized(raw_custom)
            tag = tags.get(tag_id) if tag_id else None
            if not category or (tag_id and (not tag or tag.category_id != category.pk)) or (tag_id and custom) or (not tag_id and not custom) or len(custom) > 80:
                raise forms.ValidationError('Each specialty must belong to its selected category and contain a tag or custom text.')
            key = (category.pk, tag_id, custom)
            label = tag.name if tag else custom
            identity = (category.pk, label.casefold())
            if identity in seen:
                raise forms.ValidationError('Remove duplicate specialties in the same category.')
            seen.add(identity)
            if not tag_id:
                suggested = next((t for t in tags.values() if t.category_id == category.pk and t.name.casefold() == custom.casefold()), None)
                if suggested:
                    tag_id, custom = suggested.pk, ''
            result.append({'category_id': category.pk, 'tag_id': tag_id, 'custom_text': custom})
        if len({r['category_id'] for r in result}) > 5:
            raise forms.ValidationError('Choose up to 5 skill categories.')
        return result

    def save(self):
        with transaction.atomic():
            self.profile.specialties.all().delete()
            WorkerSpecialty.objects.bulk_create([WorkerSpecialty(profile=self.profile, **row) for row in self.cleaned_data['specialties']])


def catalog_data(profile):
    return [{'id': c.pk, 'name': c.name, 'active': True, 'tags': [
        {'id': t.pk, 'name': t.name, 'active': True} for t in c.tags.all()
    ]} for c in SkillCategory.objects.prefetch_related('tags')]
