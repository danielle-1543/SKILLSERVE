from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Announcement


class AnnouncementFeedTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user(
            username="staff", password="test-password", is_staff=True
        )
        self.client.force_login(self.admin)
        self.url = reverse("CRUD_annoucements")

    def test_create_edit_pin_and_delete(self):
        response = self.client.post(self.url, {
            "action": "create", "create-title": "PESO job fair",
            "create-body": "Bring your resume.", "create-category": "job_fair",
        })
        self.assertRedirects(response, self.url)
        post = Announcement.objects.get()
        self.assertEqual(post.author, self.admin)
        self.client.post(self.url, {"action": "pin", "announcement_id": post.pk})
        post.refresh_from_db()
        self.assertTrue(post.is_pinned)
        self.client.post(self.url, {
            "action": "edit", "announcement_id": post.pk,
            f"edit-{post.pk}-title": "Updated fair",
            f"edit-{post.pk}-body": "New venue.",
            f"edit-{post.pk}-category": "job_fair",
            f"edit-{post.pk}-is_pinned": "on",
        })
        post.refresh_from_db()
        self.assertEqual(post.title, "Updated fair")
        self.client.post(self.url, {"action": "delete", "announcement_id": post.pk})
        self.assertFalse(Announcement.objects.exists())

    def test_filters_and_pinned_dialog_outside_feed(self):
        pinned = Announcement.objects.create(title="Training session", body="Details", category="training", author=self.admin, is_pinned=True)
        general = Announcement.objects.create(title="General update", body="Details", author=self.admin)
        response = self.client.get(self.url, {"category": "general", "sort": "oldest"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["post"] for row in response.context["announcement_rows"]], [general])
        self.assertContains(response, f'id="view-modal-{pinned.pk}"')
        response = self.client.get(self.url, {"start": "2099-01-01"})
        self.assertEqual(response.context["announcement_rows"], [])

    def test_invalid_submission_reopens_form(self):
        response = self.client.post(self.url, {"action": "create"})
        self.assertEqual(response.context["open_modal"], "create-modal")
        self.assertContains(response, "Please enter a title.")
        self.assertFalse(Announcement.objects.exists())

    def test_non_staff_cannot_publish(self):
        user = get_user_model().objects.create_user(username="client", password="test-password")
        self.client.force_login(user)
        response = self.client.post(self.url, {"action": "create"})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Announcement.objects.exists())
