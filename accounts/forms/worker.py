from decimal import Decimal
from pathlib import Path

from django import forms
from django.forms import inlineformset_factory
from accounts.models import WorkerProfile, WorkerService, WorkerExperience, WorkerEducation, WorkerEvidence, SkillCategory


class WorkerProfileForm(forms.ModelForm):
    class Meta:
        model = WorkerProfile
        fields = ['full_name', 'service_types', 'headline', 'location', 'phone', 'availability', 'response_time', 'service_area', 'about', 'certifications']
        labels = {'headline': 'Profile title (optional)', 'category': 'Service category', 'about': 'About you (optional)'}
        widgets = {name: forms.Textarea(attrs={'rows': 3}) for name in ('about', 'skills', 'certifications')}

    service_types = forms.ModelMultipleChoiceField(
        queryset=SkillCategory.objects.all(), widget=forms.CheckboxSelectMultiple,
        label='Types of Service', help_text='Choose up to 5 broad types of work you accept.')

    def clean_service_types(self):
        types = self.cleaned_data['service_types']
        if types.count() > 5:
            raise forms.ValidationError('Choose up to 5 types of service.')
        return types

    def clean_phone(self):
        value = self.cleaned_data['phone']
        if sum(c.isdigit() for c in value) < 7 or any(c not in '+()- .0123456789' for c in value):
            raise forms.ValidationError('Enter a valid phone number.')
        return value


class ServiceForm(forms.ModelForm):
    def __init__(self, *args, service_types=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['service_type'].queryset = service_types if service_types is not None else SkillCategory.objects.all()
        self.fields['service_type'].required = True
        self.fields['name'].help_text = 'Describe a task you offer, in your own words.'
        self.fields['starting_rate'].help_text = 'Include per hour, per visit, or per job in the service name.'

    class Meta:
        model = WorkerService
        fields = ['service_type', 'name', 'starting_rate']
        labels = {'service_type': 'Type of Service', 'name': 'Service Offered', 'starting_rate': 'Starting rate (PHP)'}

    def clean_starting_rate(self):
        rate = self.cleaned_data['starting_rate']
        if rate < Decimal('0'):
            raise forms.ValidationError('The starting rate cannot be negative.')
        return rate


class EvidenceForm(forms.ModelForm):
    class Meta:
        model = WorkerEvidence
        fields = ['label', 'file']
        labels = {'label': 'Document or proof description'}
        widgets = {'file': forms.FileInput(attrs={'accept': '.pdf,.jpg,.jpeg,.png,.webp,.mp4,.webm'})}

    def clean_file(self):
        upload = self.cleaned_data.get('file')
        if not upload or not hasattr(upload, 'temporary_file_path') and not hasattr(upload, 'content_type'):
            return upload
        if upload.size > 25 * 1024 * 1024:
            raise forms.ValidationError('Each file must be no larger than 25 MB.')
        ext = Path(upload.name).suffix.lower()
        header = upload.read(32)
        upload.seek(0)
        valid = False
        if ext == '.pdf':
            valid = header.startswith(b'%PDF-')
        elif ext == '.mp4':
            valid = header[4:8] == b'ftyp'
        elif ext == '.webm':
            valid = header.startswith(b'\x1a\x45\xdf\xa3') and b'webm' in header.lower()
        elif ext in {'.jpg', '.jpeg', '.png', '.webp'}:
            from PIL import Image
            try:
                image = Image.open(upload)
                valid = image.format in {'.jpg': {'JPEG'}, '.jpeg': {'JPEG'}, '.png': {'PNG'}, '.webp': {'WEBP'}}[ext]
                image.verify()
            except Exception:
                valid = False
            finally:
                upload.seek(0)
        if not valid:
            raise forms.ValidationError('Upload a valid PDF, JPG, PNG, WebP, MP4, or WebM file.')
        return upload

ServiceFormSet = inlineformset_factory(WorkerProfile, WorkerService, form=ServiceForm, extra=1, min_num=1, validate_min=True, max_num=20, validate_max=True)

ExperienceFormSet = inlineformset_factory(WorkerProfile, WorkerExperience, fields=['title', 'company', 'years', 'note'], widgets={'note': forms.Textarea(attrs={'rows': 2})}, extra=1, max_num=20, validate_max=True)

EducationFormSet = inlineformset_factory(WorkerProfile, WorkerEducation, fields=['program', 'school'], extra=1, max_num=20, validate_max=True)

EvidenceFormSet = inlineformset_factory(WorkerProfile, WorkerEvidence, form=EvidenceForm, extra=1, max_num=10, validate_max=True)
