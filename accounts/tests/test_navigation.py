from django.test import TestCase
from django.urls import reverse
from accounts.models import User


class NavigationTests(TestCase):
    def test_signed_in_navigation_is_shared_on_peso_and_account_pages(self):
        for role in ('client', 'worker', 'admin'):
            user = User.objects.create_user(username=f'nav-{role}', role=role, is_staff=role == 'admin')
            self.client.force_login(user)
            page_names = ['landing', 'skillserve_landing']
            page_names.append('admin_dashboard' if role == 'admin' else 'job_offers')
            for name in page_names:
                response = self.client.get(reverse(name))
                self.assertContains(response, 'id="ss-navigation"', count=1)
                self.assertNotContains(response, 'class="public-header"')
                self.assertContains(response, 'aria-label="Account navigation"', count=1)
                self.assertNotContains(response, '>Saved workers</a>')
            self.client.logout()

    def test_anonymous_public_pages_keep_top_navigation(self):
        for name in ('landing', 'skillserve_landing'):
            response = self.client.get(reverse(name))
            self.assertContains(response, 'class="public-header"')
            self.assertNotContains(response, 'id="ss-navigation"')
