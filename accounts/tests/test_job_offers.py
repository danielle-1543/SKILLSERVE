from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from accounts.models import User, WorkerProfile, JobOffer, JobComment, Conversation, JobAttachment
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import InMemoryStorage
from unittest.mock import patch


class JobOfferTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='job-client', role='client')
        self.other = User.objects.create_user(username='other-client', role='client')
        self.worker = User.objects.create_user(username='job-worker', role='worker')
        self.profile = WorkerProfile.objects.create(user=self.worker, full_name='Local Worker')
        self.data = {'title': 'Repair a leaking sink', 'job_type': 'Plumbing', 'description': 'Replace the worn fitting.', 'area': 'Quezon City', 'scheduled_at': (timezone.localtime() + timedelta(days=3)).strftime('%Y-%m-%dT%H:%M'), 'preferences': 'Bring tools', 'budget': '800'}
        self.offer = JobOffer.objects.create(client=self.owner, title='Existing job', job_type='Cleaning', description='Basic cleaning', area='Manila', scheduled_at=timezone.now()+timedelta(days=2))

    def test_client_publishes_and_worker_browses_searches_comments(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse('create_job_offer'), self.data)
        offer = JobOffer.objects.get(title=self.data['title'])
        self.assertRedirects(response, reverse('job_offer_detail', args=[offer.pk]))
        self.assertEqual(offer.client, self.owner)
        self.client.force_login(self.worker)
        response = self.client.get(reverse('job_offers'), {'q': 'Plumbing'})
        self.assertContains(response, offer.title)
        self.assertNotContains(response, 'Existing job')
        self.assertContains(self.client.get(reverse('job_offer_detail', args=[offer.pk])), 'Message client')
        self.client.post(reverse('job_offer_detail', args=[offer.pk]), {'body': 'I can bring tools.'})
        self.assertTrue(JobComment.objects.filter(offer=offer, author=self.worker).exists())

    def test_role_and_ownership_permissions(self):
        self.assertEqual(self.client.get(reverse('job_offers')).status_code, 302)
        self.client.force_login(self.worker)
        self.assertEqual(self.client.post(reverse('create_job_offer'), self.data).status_code, 403)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse('job_offer_detail', args=[self.offer.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('close_job_offer', args=[self.offer.pk])).status_code, 404)
        self.assertNotContains(self.client.get(reverse('job_offers')), 'Existing job')

    def test_chat_reuses_participant_conversation_and_closed_offer_blocks_actions(self):
        self.client.force_login(self.worker)
        url = reverse('message_job_client', args=[self.offer.pk])
        self.client.post(url)
        self.client.post(url)
        thread = Conversation.objects.get(client=self.owner, worker=self.profile)
        self.assertContains(self.client.get(reverse('conversation', args=[thread.pk])), self.owner.username)
        self.client.force_login(self.owner)
        self.client.post(reverse('close_job_offer', args=[self.offer.pk]))
        self.client.force_login(self.worker)
        self.assertNotContains(self.client.get(reverse('job_offers')), 'Existing job')
        self.assertEqual(self.client.post(url).status_code, 403)
        self.assertEqual(self.client.post(reverse('job_offer_detail', args=[self.offer.pk]), {'body':'Late comment'}).status_code, 403)

    def test_invalid_schedule_and_budget_do_not_publish(self):
        self.client.force_login(self.owner)
        self.data['scheduled_at'] = (timezone.now()-timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
        self.data['budget'] = '-1'
        response = self.client.post(reverse('create_job_offer'), self.data)
        self.assertContains(response, 'Choose a future date and time.')
        self.assertEqual(JobOffer.objects.count(), 1)

    def test_upload_saved_displayed_and_protected(self):
        self.client.force_login(self.owner)
        field = JobAttachment._meta.get_field('file')
        with patch.object(field, 'storage', InMemoryStorage()):
            payload = dict(self.data, attachments=SimpleUploadedFile('job-details.txt', b'Bring cleaning tools.', content_type='text/plain'))
            self.client.post(reverse('create_job_offer'), payload)
            attachment = JobAttachment.objects.get()
            url = reverse('job_attachment', args=[attachment.pk])
            self.assertContains(self.client.get(reverse('job_offer_detail', args=[attachment.offer_id])), 'job-details.txt')
            self.client.force_login(self.worker)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(b''.join(response.streaming_content), b'Bring cleaning tools.')
            self.client.force_login(self.other)
            self.assertEqual(self.client.get(url).status_code, 404)
            self.client.logout()
            self.assertEqual(self.client.get(url).status_code, 302)

    def test_invalid_attachment_rejects_whole_post(self):
        self.client.force_login(self.owner)
        payload = dict(self.data, attachments=SimpleUploadedFile('fake.jpg', b'not an image'))
        response = self.client.post(reverse('create_job_offer'), payload)
        self.assertContains(response, 'Use a valid JPG')
        self.assertEqual(JobOffer.objects.count(), 1)
        self.assertEqual(JobAttachment.objects.count(), 0)
