import tempfile
import json
from pathlib import Path
from django.contrib.auth import get_user_model
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from accounts.models import WorkerProfile, WorkerService, WorkerEvidence, WorkerReview, SkillCategory


class WorkerProfileFlowTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.worker = User.objects.create_user(username='worker', password='Test-pass-2841!', role='worker')
        self.admin = User.objects.create_user(username='admin-review', password='Test-pass-2841!', is_staff=True, role='admin')
        self.client_user = User.objects.create_user(username='client', role='client')
        self.client.force_login(self.worker)
        self.profile = WorkerProfile.objects.create(user=self.worker)
        self.category = SkillCategory.objects.create(name='Electrical', slug='electrical')
        self.tmp = tempfile.TemporaryDirectory()
        field = WorkerEvidence._meta.get_field('file')
        original_storage = field.storage
        field.storage = FileSystemStorage(location=self.tmp.name)
        self.addCleanup(setattr, field, 'storage', original_storage)
        self.addCleanup(self.tmp.cleanup)

    def payload(self):
        return {
            'revision': str(self.profile.revision),
            'service_types': [str(self.category.pk)],
            'services-0-service_type': str(self.category.pk),
            'specialties': json.dumps([{'category': self.category.pk, 'tag': None, 'custom': 'Residential wiring'}]),
            'full_name': 'Camille Reyes', 'headline': 'Skilled local electrician',
            'category': 'Electrical services', 'location': 'Local community',
            'phone': '09171234567', 'about': 'Residential electrical repair.',
            'skills': 'Wiring, repairs', 'certifications': 'Skills certificate',
            'services-TOTAL_FORMS': '1', 'services-INITIAL_FORMS': '0',
            'services-0-name': 'Electrical repair', 'services-0-starting_rate': '500.00',
            'experience-TOTAL_FORMS': '1', 'experience-INITIAL_FORMS': '0',
            'experience-0-title': 'Electrician', 'experience-0-company': 'Self employed',
            'experience-0-years': '2020–2026', 'experience-0-note': 'Home repairs',
            'education-TOTAL_FORMS': '1', 'education-INITIAL_FORMS': '0',
            'education-0-program': 'Electrical training', 'education-0-school': 'Training center',
            'evidence-TOTAL_FORMS': '0', 'evidence-INITIAL_FORMS': '0',
        }

    def submit(self):
        response = self.client.post(reverse('edit_worker_profile'), self.payload())
        self.assertRedirects(response, reverse('worker_profile'))
        self.profile.refresh_from_db()
        return response

    def test_complete_profile_submitted_and_visible_to_admin(self):
        self.submit()
        self.assertEqual(self.profile.status, 'pending')
        self.assertEqual(self.profile.revision, 1)
        self.assertEqual(self.profile.services.get().starting_rate, 500)
        self.assertEqual(self.profile.experiences.get().title, 'Electrician')
        self.assertEqual(self.profile.education.get().program, 'Electrical training')
        self.client.force_login(self.admin)
        response = self.client.get(reverse('worker_reviews'))
        self.assertContains(response, 'Camille Reyes')
        response = self.client.get(reverse('review_worker', args=[self.profile.pk]))
        self.assertContains(response, 'Electrical repair')
        self.assertContains(response, 'Feedback / suggestions / reason')

    def test_all_review_decisions_and_feedback_history(self):
        self.submit()
        self.client.force_login(self.admin)
        url = reverse('review_worker', args=[self.profile.pk])
        for decision in ('changes', 'rejected', 'approved'):
            self.profile.status = 'pending'
            self.profile.revision += 1
            self.profile.save()
            response = self.client.post(url, {'revision': self.profile.revision, 'decision': decision, 'feedback': 'Please clarify your certification.'})
            self.assertRedirects(response, url)
            self.profile.refresh_from_db()
            self.assertEqual(self.profile.status, decision)
        self.assertEqual(WorkerReview.objects.count(), 3)
        self.client.force_login(self.worker)
        response = self.client.get(reverse('worker_profile'))
        self.assertContains(response, 'Please clarify your certification.')

    def test_feedback_required_and_stale_review_rejected(self):
        self.submit()
        self.client.force_login(self.admin)
        url = reverse('review_worker', args=[self.profile.pk])
        for data in ({'revision': 1, 'decision': 'changes', 'feedback': ''}, {'revision': 0, 'decision': 'approved', 'feedback': 'Reviewed'}):
            response = self.client.post(url, data)
            self.assertEqual(response.status_code, 200)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.status, 'pending')
        self.assertFalse(WorkerReview.objects.exists())

    def test_resubmission_returns_to_pending_and_preserves_history(self):
        self.submit()
        self.client.force_login(self.admin)
        self.client.post(reverse('review_worker', args=[self.profile.pk]), {'revision': 1, 'decision': 'changes', 'feedback': 'Update your headline.'})
        self.client.force_login(self.worker)
        self.profile.refresh_from_db()
        data = self.payload()
        service = self.profile.services.get()
        data.update({'services-INITIAL_FORMS': '1', 'services-0-id': str(service.pk), 'headline': 'Updated headline', 'experience-TOTAL_FORMS': '0', 'experience-INITIAL_FORMS': '0', 'education-TOTAL_FORMS': '0', 'education-INITIAL_FORMS': '0'})
        self.assertRedirects(self.client.post(reverse('edit_worker_profile'), data), reverse('worker_profile'))
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.status, 'pending')
        self.assertEqual(self.profile.revision, 2)
        self.assertEqual(self.profile.reviews.count(), 1)
        self.assertEqual(self.profile.services.count(), 1)

    def test_invalid_profile_cannot_submit_or_set_approved_status(self):
        data = self.payload()
        data.update({'status': 'approved', 'services-0-starting_rate': '-1'})
        response = self.client.post(reverse('edit_worker_profile'), data)
        self.assertContains(response, 'cannot be negative')
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.status, 'draft')
        self.assertFalse(self.profile.services.exists())

    def test_proof_upload_and_private_inline_preview(self):
        data = self.payload()
        data.update({'evidence-TOTAL_FORMS': '1', 'evidence-0-label': 'Certificate', 'evidence-0-file': SimpleUploadedFile('certificate.pdf', b'%PDF-1.4\ncertificate', content_type='application/pdf')})
        self.assertRedirects(self.client.post(reverse('edit_worker_profile'), data), reverse('worker_profile'))
        evidence = self.profile.evidence.get()
        self.assertTrue(Path(evidence.file.path).exists())
        url = reverse('worker_evidence', args=[evidence.pk])
        page = self.client.get(reverse('worker_profile'))
        self.assertContains(page, 'class="proof-document"')
        self.assertNotContains(page, 'Download file')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response['Content-Disposition'].startswith('inline'))
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertEqual(response['X-Frame-Options'], 'SAMEORIGIN')
        response.close()
        self.client.force_login(self.client_user)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.force_login(self.admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response['Content-Disposition'].startswith('inline'))
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertEqual(response['X-Frame-Options'], 'SAMEORIGIN')
        response.close()
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 302)

    def test_fake_upload_is_rejected(self):
        data = self.payload()
        data.update({'evidence-TOTAL_FORMS': '1', 'evidence-0-label': 'Fake certificate', 'evidence-0-file': SimpleUploadedFile('proof.png', b'not an image', content_type='image/png')})
        response = self.client.post(reverse('edit_worker_profile'), data)
        self.assertContains(response, 'Upload a valid PDF')
        self.assertFalse(WorkerEvidence.objects.exists())
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.status, 'draft')

    def test_access_roles_and_worker_login_destination(self):
        self.assertEqual(self.client.get(reverse('review_worker', args=[self.profile.pk])).status_code, 403)
        self.client.force_login(self.client_user)
        self.assertEqual(self.client.get(reverse('edit_worker_profile')).status_code, 403)
        self.assertEqual(self.client.get(reverse('worker_profile')).status_code, 403)
        self.client.logout()
        response = self.client.post(reverse('login'), {'username': 'worker', 'password': 'Test-pass-2841!', 'next': '/dashboard/'})
        self.assertRedirects(response, reverse('edit_worker_profile'))

    def test_duplicate_review_is_not_applied_twice(self):
        self.submit()
        self.client.force_login(self.admin)
        url = reverse('review_worker', args=[self.profile.pk])
        data = {'revision': 1, 'decision': 'approved', 'feedback': 'Verified certificate.'}
        self.client.post(url, data)
        self.client.post(url, data)
        self.assertEqual(WorkerReview.objects.count(), 1)
