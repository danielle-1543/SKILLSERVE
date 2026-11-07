from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import Announcement


class LoginFlowTests(TestCase):
    def setUp(self):
        self.member = get_user_model().objects.create_user(username="member", password="test-password")
        self.admin = get_user_model().objects.create_user(username="admin", password="test-password", is_staff=True)
        Announcement.objects.create(title="Public PESO news", body="Everyone can read this", author=self.admin)

    def test_public_landing_needs_no_login(self):
        response = self.client.get(reverse("landing"))
        self.assertContains(response, "Public PESO news")
        self.assertNotContains(response, 'id="member-login"')
        self.assertNotContains(response, 'name="action" value="delete"')

    def test_member_login_opens_popup_and_redirects_to_member_dashboard(self):
        response = self.client.get(reverse("login"))
        self.assertTrue(response.context["open_login"])
        response = self.client.post(reverse("login"), {"username": "member", "password": "test-password"})
        self.assertRedirects(response, reverse("skillserve_dashboard"))

    def test_old_admin_login_redirects_to_shared_modal(self):
        response = self.client.get(reverse('admin_login'), {'next':'/admin-dashboard/skills/'})
        self.assertRedirects(response, reverse('login')+'?next=%2Fadmin-dashboard%2Fskills%2F')
        self.assertRedirects(self.client.get('/admin/login/'), reverse('login'))
        response = self.client.post(reverse('login'), {'username':'admin','password':'test-password'})
        self.assertRedirects(response, reverse('admin_dashboard'))

    def test_protected_pages_use_the_correct_login(self):
        response = self.client.get(reverse("skillserve_dashboard"))
        self.assertRedirects(response, reverse("login") + "?next=/dashboard/")
        response = self.client.get(reverse("CRUD_annoucements"))
        self.assertRedirects(response, reverse("login") + "?next=/admin-dashboard/announcements/")
        self.client.force_login(self.member)
        response = self.client.get(reverse("CRUD_annoucements"))
        self.assertEqual(response.status_code, 403)

    def test_invalid_member_login_keeps_popup_open(self):
        response = self.client.post(reverse("login"), {"username": "member", "password": "wrong"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.assertTrue(response.context["open_login"])

    def test_logout_returns_to_public_dashboard(self):
        self.client.force_login(self.member)
        self.assertRedirects(self.client.post(reverse("logout")), reverse("landing"))

    def test_general_is_default_and_categories_query_database(self):
        training = Announcement.objects.create(title="Training opportunity", body="Skills training", category="training", author=self.admin)
        response = self.client.get(reverse("landing"))
        self.assertEqual(response.context["selected_category"], "general")
        self.assertContains(response, "Public PESO news")
        self.assertNotContains(response, "Training opportunity")
        response = self.client.get(reverse("landing"), {"category": "training"})
        self.assertContains(response, training.title)
        self.assertNotContains(response, "Public PESO news")
        response = self.client.get(reverse("landing"), {"category": "all"})
        self.assertContains(response, training.title)
        self.assertContains(response, "Public PESO news")
        response = self.client.get(reverse("landing"), {"category": "invalid"})
        self.assertEqual(response.context["selected_category"], "general")

    def test_peso_navigation_and_separate_skillserve_landing(self):
        response = self.client.get(reverse("landing"))
        self.assertContains(response, 'href="#contact-us"')
        self.assertContains(response, 'id="contact-us"')
        self.assertContains(response, 'href="https://peis.philjobnet.gov.ph/"')
        self.assertContains(response, 'href="/skillserve/"', count=2)
        self.assertNotContains(response, "Welcome to SkillServe")
        self.assertNotContains(response, "Log in to SkillServe")
        response = self.client.get(reverse("skillserve_landing"))
        self.assertContains(response, 'id="member-login"')
        self.assertEqual(response.status_code, 200)


class SignUpTests(TestCase):
    def payload(self, role):
        return {"role": role, "username": "newperson", "email": "person@example.com", "first_name": "New", "last_name": "Person", "password1": "Sample-pass-7824!", "password2": "Sample-pass-7824!", "is_staff": "true", "is_superuser": "true"}

    def test_worker_and_client_registration(self):
        for role in ("worker", "client"):
            with self.subTest(role=role):
                self.client.logout()
                response = self.client.post(reverse("signup"), self.payload(role))
                self.assertRedirects(response, reverse("edit_worker_profile" if role == "worker" else "login"))
                user = get_user_model().objects.get(username="newperson")
                self.assertEqual(user.role, role)
                self.assertTrue(user.check_password("Sample-pass-7824!"))
                self.assertFalse(user.is_staff)
                self.assertFalse(user.is_superuser)
                user.delete()

    def test_role_required_and_admin_role_rejected(self):
        for role in ("", "admin"):
            response = self.client.post(reverse("signup"), self.payload(role))
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context["form"].errors)
        self.assertFalse(get_user_model().objects.exists())

    def test_duplicate_username_and_password_validation(self):
        self.client.post(reverse("signup"), self.payload("client"))
        response = self.client.post(reverse("signup"), self.payload("worker"))
        self.assertIn("username", response.context["form"].errors)
        data = self.payload("worker")
        data.update(username="another", password2="mismatch")
        response = self.client.post(reverse("signup"), data)
        self.assertIn("password2", response.context["form"].errors)
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_role_preselection_and_signup_link(self):
        response = self.client.get(reverse("signup"), {"role": "worker"})
        self.assertEqual(response.context["form"]["role"].value(), "worker")
        response = self.client.get(reverse("login"))
        self.assertContains(response, "Sign up!")
        self.assertContains(response, 'href="/signup/"')

class AdministratorRoutingTests(TestCase):
    def test_admin_login_always_uses_admin_dashboard(self):
        get_user_model().objects.create_user(username="routing-admin", password="Routing-pass-7842!", role="admin", is_staff=True)
        for login_name in ("login",):
            self.client.logout()
            response = self.client.post(reverse(login_name), {"username": "routing-admin", "password": "Routing-pass-7842!", "next": "/dashboard/"})
            self.assertRedirects(response, reverse("admin_dashboard"))
            self.assertRedirects(self.client.get(reverse("skillserve_dashboard")), reverse("admin_dashboard"))

class SharedRoleLoginTests(TestCase):
    def test_admin_role_uses_shared_login_without_staff_flag(self):
        user = get_user_model().objects.create_user(username='role-admin', password='Role-pass-3142!', role='admin')
        response = self.client.post(reverse('login'), {'username':user.username,'password':'Role-pass-3142!'})
        self.assertRedirects(response, reverse('admin_dashboard'))
        self.assertEqual(self.client.get(reverse('skills_catalog')).status_code, 200)

    def test_client_cannot_use_next_to_enter_admin_area(self):
        get_user_model().objects.create_user(username='role-client', password='Role-pass-3142!', role='client')
        response = self.client.post(reverse('login'), {'username':'role-client','password':'Role-pass-3142!','next':'/admin-dashboard/skills/'})
        self.assertRedirects(response, reverse('skillserve_dashboard'))
        self.assertEqual(self.client.get(reverse('skills_catalog')).status_code, 403)


class PublicShareTests(TestCase):
    def test_share_link_opens_specific_post_without_login(self):
        author = get_user_model().objects.create_user(username="share-author", is_staff=True)
        post = Announcement.objects.create(title="Share this training", body="Full public details", category="training", author=author)
        url = reverse("public_announcement", args=[post.pk])
        response = self.client.get(reverse("landing"), {"category": "training"})
        self.assertContains(response, f'data-share-url="{url}"')
        response = self.client.get(url)
        self.assertContains(response, "Share this training")
        self.assertContains(response, "Full public details")
        self.assertContains(response, f'data-share-url="{url}"')
        self.assertEqual(self.client.get(reverse("public_announcement", args=[999999])).status_code, 404)
