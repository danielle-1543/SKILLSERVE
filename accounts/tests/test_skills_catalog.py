import json
from django.test import TestCase
from django.urls import reverse
from accounts.forms.skills import WorkerSkillsForm, CategoryForm
from accounts.models import User, WorkerProfile, SkillCategory, SpecialtyTag, WorkerSpecialty


class SkillsCatalogTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='catalog-admin', is_staff=True, role='admin')
        self.worker = User.objects.create_user(username='catalog-worker', role='worker')
        self.client_user = User.objects.create_user(username='catalog-client', role='client')
        self.profile = WorkerProfile.objects.create(user=self.worker, full_name='Local Worker', status='approved')
        self.category = SkillCategory.objects.create(name='Plumbing', slug='plumbing')
        self.tag = SpecialtyTag.objects.create(category=self.category, name='Leak repair')

    def skills_form(self, rows):
        return WorkerSkillsForm({'specialties': json.dumps(rows)}, profile=self.profile)

    def test_admin_crud_and_used_entries_are_protected(self):
        url = reverse('skills_catalog')
        self.client.force_login(self.worker)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(url), 'Plumbing')
        self.client.post(url, {'kind':'category','action':'save','name':'Cleaning','specialties':'Deep cleaning'})
        category = SkillCategory.objects.get(slug='cleaning')
        self.client.post(url, {'kind':'tag','action':'save','category':category.pk,'name':'Deep cleaning','is_active':'on'})
        tag = SpecialtyTag.objects.get(name='Deep cleaning')
        self.client.post(url, {'kind':'tag','action':'save','entry_id':tag.pk,'category':category.pk,'name':'House deep cleaning','is_active':'on'})
        tag.refresh_from_db()
        self.assertEqual(tag.name, 'House deep cleaning')
        WorkerSpecialty.objects.create(profile=self.profile, category=category, tag=tag)
        self.client.post(url, {'kind':'tag','action':'delete','entry_id':tag.pk})
        self.assertTrue(SpecialtyTag.objects.filter(pk=tag.pk).exists())
        self.client.post(url, {'kind':'tag','action':'toggle','entry_id':tag.pk})
        tag.refresh_from_db()
        self.assertTrue(SpecialtyTag.objects.filter(pk=tag.pk).exists())
        self.client.post(url, {'kind':'category','action':'delete','entry_id':category.pk})
        self.assertTrue(SkillCategory.objects.filter(pk=category.pk).exists())
        unused = SkillCategory.objects.create(name='Unused', slug='unused')
        self.client.post(url, {'kind':'category','action':'delete','entry_id':unused.pk})
        self.assertFalse(SkillCategory.objects.filter(pk=unused.pk).exists())

    def test_slug_is_generated_and_kept_stable(self):
        form = CategoryForm({'name': 'Home Repair', 'specialties':'Repair'})
        self.assertNotIn('slug', form.fields)
        self.assertTrue(form.is_valid(), form.errors)
        category = form.save()
        self.assertEqual(category.slug, 'home-repair')
        edit = CategoryForm({'name':'Home Repairs and Maintenance', 'specialties':'Repair'}, instance=category)
        self.assertTrue(edit.is_valid(), edit.errors)
        self.assertEqual(edit.save().slug, 'home-repair')
        collision = CategoryForm({'name':'Home-Repair','specialties':'Repair'})
        self.assertTrue(collision.is_valid(), collision.errors)
        self.assertEqual(collision.save().slug, 'home-repair-2')

    def test_suggested_custom_tags_and_duplicate_validation(self):
        rows = [{'category':self.category.pk,'tag':self.tag.pk,'custom':''}, {'category':self.category.pk,'tag':None,'custom':'  Water   tank installation  '}]
        form = self.skills_form(rows)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertEqual(self.profile.specialties.count(), 2)
        self.assertEqual(SpecialtyTag.objects.count(), 1)
        self.assertTrue(self.profile.specialties.filter(custom_text='Water tank installation').exists())
        self.assertFalse(self.skills_form(rows+[rows[0]]).is_valid())
        self.assertFalse(self.skills_form(rows+[{'category':self.category.pk,'custom':'leak REPAIR'}]).is_valid())
        category = SkillCategory.objects.create(name='Electrical', slug='electrical')
        self.assertFalse(self.skills_form([{'category':category.pk,'tag':self.tag.pk}]).is_valid())
        self.assertFalse(self.skills_form([]).is_valid())
        self.assertFalse(self.skills_form([{'category':999999,'custom':'Anything'}]).is_valid())

    def test_removed_controls_and_actions(self):
        self.client.force_login(self.admin)
        url = reverse('skills_catalog')
        response = self.client.get(url)
        self.assertNotContains(response, 'Deactivate')
        self.assertNotContains(response, 'Worker-submitted specialties')
        self.assertNotContains(response, 'name="is_active"')
        for action in ('toggle', 'promote'):
            self.assertEqual(self.client.post(url, {'action':action,'kind':'tag','entry_id':self.tag.pk}).status_code, 400)

    def test_category_and_specialties_saved_atomically(self):
        self.client.force_login(self.admin)
        url = reverse('skills_catalog')
        response = self.client.post(url, {'action':'save','kind':'category','name':'Carpentry','specialties':'Cabinet making\nFurniture repair'})
        self.assertRedirects(response, url)
        category = SkillCategory.objects.get(name='Carpentry')
        self.assertEqual(category.tags.count(), 2)
        response = self.client.post(url, {'action':'save','kind':'category','name':'Bad category','specialties':'Duplicate\nduplicate'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(SkillCategory.objects.filter(name='Bad category').exists())
        WorkerSpecialty.objects.create(profile=self.profile, category=category, tag=category.tags.get(name='Cabinet making'))
        self.client.post(url, {'action':'save','kind':'category','entry_id':category.pk,'name':'Changed name','specialties':'Furniture repair'})
        category.refresh_from_db()
        self.assertEqual(category.name, 'Carpentry')
        self.assertEqual(category.tags.count(), 2)

    def test_used_tag_cannot_be_moved_and_specialties_are_searchable(self):
        WorkerSpecialty.objects.create(profile=self.profile, category=self.category, tag=self.tag)
        WorkerSpecialty.objects.create(profile=self.profile, category=self.category, custom_text='Water tank installation')
        self.client.force_login(self.client_user)
        for query in ('Leak repair', 'Water tank', 'Plumbing'):
            self.assertContains(self.client.get(reverse('search_workers'), {'q':query}), 'Local Worker')
        self.assertContains(self.client.get(reverse('search_workers'), {'category':'plumbing'}), 'Local Worker')
        response = self.client.get(reverse('client_worker_profile', args=[self.profile.pk]))
        self.assertContains(response, 'Water tank installation')
        self.client.force_login(self.admin)
        category = SkillCategory.objects.create(name='Cleaning', slug='cleaning')
        self.client.post(reverse('skills_catalog'), {'kind':'tag','action':'save','entry_id':self.tag.pk,'category':category.pk,'name':'Leak repair','is_active':'on'})
        self.tag.refresh_from_db()
        self.assertEqual(self.tag.category_id, self.category.pk)
