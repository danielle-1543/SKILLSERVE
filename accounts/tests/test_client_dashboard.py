from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from accounts.models import WorkerProfile, WorkerService
from core.models import Announcement


class ClientDashboardTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='dashboard-client', role='client')
        self.worker = User.objects.create_user(username='approved-worker', role='worker')
        self.pending = User.objects.create_user(username='pending-worker', role='worker')
        self.profile = WorkerProfile.objects.create(user=self.worker, full_name='Local Professional', category='Plumbing', location='Quezon City', status='approved')
        WorkerService.objects.create(profile=self.profile, name='Pipe repair', starting_rate=350)
        WorkerProfile.objects.create(user=self.pending, full_name='Pending Applicant', category='Plumbing', status='pending')
        self.client.force_login(self.user)

    def test_layout_order_and_database_announcements(self):
        Announcement.objects.create(author=self.user, title='Upcoming job fair', body='Visit the job fair.')
        response = self.client.get(reverse('skillserve_dashboard'))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertLess(html.index('id="worker-search"'), html.index('id="service-categories"'))
        self.assertLess(html.index('id="service-categories"'), html.index('id="recent-announcements"'))
        self.assertContains(response, 'Upcoming job fair')
        self.assertContains(response, 'client_dashboard.css')

    def test_category_search_only_shows_verified_workers(self):
        response = self.client.get(reverse('search_workers'), {'category': 'plumbing'})
        self.assertContains(response, 'Local Professional')
        self.assertContains(response, 'Pipe repair')
        self.assertNotContains(response, 'Pending Applicant')
        self.assertEqual(response.context['worker_count'], 1)

    def test_keyword_location_and_empty_search(self):
        url = reverse('search_workers')
        response = self.client.get(url, {'q': 'pipe', 'location': 'Quezon'})
        self.assertContains(response, 'Local Professional')
        self.assertEqual(response.context['worker_count'], 1)
        response = self.client.get(url, {'category': 'tutoring'})
        self.assertContains(response, 'No verified workers found yet')
        self.assertEqual(response.context['worker_count'], 0)
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 302)

    def test_name_username_and_extra_spaces(self):
        self.worker.first_name = 'Daniela'
        self.worker.last_name = 'Romualdo'
        self.worker.save()
        self.profile.full_name = 'Daniela Romualdo'
        self.profile.save()
        for query in ('Daniela', 'romualdo', 'Romualdo  Daniela', 'approved-worker', 'Daniela   Romualdo'):
            response = self.client.get(reverse('search_workers'), {'q': query})
            self.assertEqual(response.context['worker_count'], 1, query)
            self.assertContains(response, 'Daniela Romualdo')
