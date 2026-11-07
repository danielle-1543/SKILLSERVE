from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from accounts.models import WorkerProfile, WorkerReview, WorkerPost, Conversation, ChatMessage, SavedWorker, UserReport


class ClientWorkerInteractionTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.customer = User.objects.create_user(username='customer', role='client')
        self.stranger = User.objects.create_user(username='stranger', role='client')
        self.worker = User.objects.create_user(username='worker-view', role='worker')
        self.admin = User.objects.create_user(username='report-admin', is_staff=True, role='admin')
        self.profile = WorkerProfile.objects.create(user=self.worker, full_name='Visible Worker', status='approved', skills='Plumbing', about='Worker resume content')
        WorkerReview.objects.create(profile=self.profile, reviewer=self.admin, revision=1, decision='approved', feedback='Private verification feedback')
        WorkerPost.objects.create(profile=self.profile, body='My public work update')
        self.client.force_login(self.customer)

    def test_dedicated_search_and_clickable_profiles(self):
        response = self.client.get(reverse('search_workers'), {'q': 'Plumbing'})
        self.assertContains(response, reverse('client_worker_profile', args=[self.profile.pk]))
        self.assertTemplateUsed(response, 'clients/search.html')
        response = self.client.get(reverse('skillserve_dashboard'), {'q': 'Plumbing'})
        self.assertRedirects(response, reverse('search_workers') + '?q=Plumbing')

    def test_resume_posts_reviews_hide_private_proof_and_verification(self):
        url = reverse('client_worker_profile', args=[self.profile.pk])
        response = self.client.get(url)
        self.assertContains(response, 'Worker resume content')
        self.assertNotContains(response, 'Private verification feedback')
        self.assertNotContains(response, 'Proof and certification files')
        response = self.client.get(url, {'tab': 'posts'})
        self.assertContains(response, 'My public work update')
        self.assertNotContains(response, 'Post update')
        response = self.client.get(url, {'tab': 'reviews'})
        self.assertContains(response, 'No ratings yet')
        self.profile.status = 'pending'
        self.profile.save()
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_bookmark_persists_and_toggles(self):
        url = reverse('bookmark_worker', args=[self.profile.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.post(url)
        self.assertTrue(SavedWorker.objects.filter(client=self.customer, worker=self.profile).exists())
        self.assertContains(self.client.get(reverse('saved_workers')), 'Visible Worker')
        self.client.post(url)
        self.assertFalse(SavedWorker.objects.exists())

    def test_private_messages_both_participants_and_no_third_party(self):
        self.client.post(reverse('start_conversation', args=[self.profile.pk]))
        self.client.post(reverse('start_conversation', args=[self.profile.pk]))
        self.assertEqual(Conversation.objects.count(), 1)
        thread = Conversation.objects.get()
        url = reverse('conversation', args=[thread.pk])
        self.client.post(url, {'body': 'Can you help with plumbing?'})
        self.assertEqual(ChatMessage.objects.get().sender, self.customer)
        self.client.force_login(self.worker)
        self.assertContains(self.client.get(reverse('inbox')), 'customer')
        self.assertContains(self.client.get(url), 'Can you help with plumbing?')
        self.client.post(url, {'body': 'Yes, please describe the issue.'})
        self.client.force_login(self.stranger)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url, {'body': 'Unauthorized'}).status_code, 404)
        self.assertEqual(ChatMessage.objects.count(), 2)

    def test_report_goes_to_admin_and_not_worker(self):
        url = reverse('report_worker', args=[self.profile.pk])
        self.client.post(url, {'reason': 'misleading', 'details': 'Please check this information.'})
        report = UserReport.objects.get()
        self.assertEqual(report.reporter, self.customer)
        self.assertEqual(self.client.get(reverse('reported_workers')).status_code, 403)
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse('reported_workers')), 'Please check this information.')
        self.client.post(reverse('reported_workers'), {'report_id': report.pk})
        report.refresh_from_db()
        self.assertTrue(report.reviewed)
        self.client.force_login(self.worker)
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_message_validation_and_client_only_actions(self):
        self.client.post(reverse('start_conversation', args=[self.profile.pk]))
        thread = Conversation.objects.get()
        response = self.client.post(reverse('conversation', args=[thread.pk]), {'body': '   '})
        self.assertTrue(response.context['form'].errors)
        self.assertFalse(ChatMessage.objects.exists())
        self.client.force_login(self.worker)
        self.assertEqual(self.client.get(reverse('search_workers')).status_code, 403)
        self.assertEqual(self.client.post(reverse('bookmark_worker', args=[self.profile.pk])).status_code, 403)
