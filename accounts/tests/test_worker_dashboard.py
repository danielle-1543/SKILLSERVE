from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from accounts.models import WorkerProfile, WorkerPost, WorkerClientReview


class WorkerDashboardTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.worker = User.objects.create_user(username='profile-owner', role='worker')
        self.other = User.objects.create_user(username='other-worker', role='worker')
        self.client_user = User.objects.create_user(username='review-client', first_name='Camille', role='client')
        self.profile = WorkerProfile.objects.create(user=self.worker, full_name='Daniela Romualdo', skills='Data entry, Graphic design\nCustomer service')
        self.other_profile = WorkerProfile.objects.create(user=self.other)
        self.client.force_login(self.worker)

    def test_tabs_and_real_profile_data(self):
        response = self.client.get(reverse('worker_profile'))
        self.assertContains(response, 'resume-cover')
        self.assertContains(response, 'Daniela Romualdo')
        self.assertContains(response, '<span>Graphic design</span>', html=True)
        self.assertNotContains(response, 'verification-approved')
        self.assertEqual(response.context['tab'], 'resume')
        response = self.client.get(reverse('worker_profile'), {'tab': 'reviews'})
        self.assertContains(response, 'No ratings yet')
        response = self.client.get(reverse('worker_profile'), {'tab': 'bad-tab'})
        self.assertEqual(response.context['tab'], 'resume')

    def test_create_like_unlike_delete_post(self):
        url = reverse('worker_posts')
        response = self.client.post(url, {'action': 'create', 'body': 'Finished a community project.'})
        self.assertRedirects(response, reverse('worker_profile') + '?tab=posts')
        post = self.profile.posts.get()
        self.assertEqual(post.body, 'Finished a community project.')
        self.client.post(url, {'action': 'like', 'post_id': post.pk})
        self.assertTrue(post.likes.filter(pk=self.worker.pk).exists())
        self.client.post(url, {'action': 'like', 'post_id': post.pk})
        self.assertEqual(post.likes.count(), 0)
        self.client.post(url, {'action': 'delete', 'post_id': post.pk})
        self.assertFalse(WorkerPost.objects.exists())

    def test_empty_post_and_other_workers_posts_are_protected(self):
        url = reverse('worker_posts')
        response = self.client.post(url, {'action': 'create', 'body': '   '})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['post_form'].errors)
        self.assertFalse(WorkerPost.objects.exists())
        post = WorkerPost.objects.create(profile=self.other_profile, body='Other worker update')
        self.assertEqual(self.client.post(url, {'action': 'delete', 'post_id': post.pk}).status_code, 404)
        self.assertTrue(WorkerPost.objects.filter(pk=post.pk).exists())
        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.force_login(self.client_user)
        self.assertEqual(self.client.post(url, {'action': 'create', 'body': 'Not authorized'}).status_code, 403)

    def test_reviews_are_based_on_saved_client_feedback(self):
        WorkerClientReview.objects.create(profile=self.profile, client=self.client_user, rating=5, feedback='Excellent service.')
        WorkerClientReview.objects.create(profile=self.profile, client=self.client_user, rating=4, feedback='Prompt and professional.')
        response = self.client.get(reverse('worker_profile'), {'tab': 'reviews'})
        self.assertEqual(response.context['rating']['total'], 2)
        self.assertEqual(response.context['rating']['average'], 4.5)
        self.assertContains(response, 'Excellent service.')
        self.assertContains(response, '4.5')
        self.assertNotContains(response, 'No ratings yet')

class WorkerPostPhotoTests(TestCase):
    def setUp(self):
        from django.core.files.storage import InMemoryStorage
        self.worker = get_user_model().objects.create_user(username='photo-worker', role='worker')
        self.profile = WorkerProfile.objects.create(user=self.worker)
        self.client.force_login(self.worker)
        field = WorkerPost._meta.get_field('photo')
        original = field.storage
        field.storage = InMemoryStorage()
        self.addCleanup(setattr, field, 'storage', original)

    def image(self):
        from io import BytesIO
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile
        data = BytesIO()
        Image.new('RGB', (30, 20), 'blue').save(data, format='PNG')
        return SimpleUploadedFile('work.png', data.getvalue(), content_type='image/png')

    def test_photo_only_and_text_with_photo_posts(self):
        for body in ('', 'My latest project'):
            response = self.client.post(reverse('worker_posts'), {'action': 'create', 'body': body, 'photo': self.image()})
            self.assertRedirects(response, reverse('worker_profile') + '?tab=posts')
        self.assertEqual(self.profile.posts.count(), 2)
        post = self.profile.posts.first()
        self.assertTrue(post.photo)
        response = self.client.get(reverse('worker_profile'), {'tab': 'posts'})
        self.assertContains(response, 'class="work-post-photo"', count=2)
        self.assertContains(response, post.photo.url)

    def test_invalid_image_does_not_publish(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        response = self.client.post(reverse('worker_posts'), {'action': 'create', 'body': 'An image', 'photo': SimpleUploadedFile('fake.png', b'not-an-image', content_type='image/png')})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['post_form'].errors)
        self.assertFalse(WorkerPost.objects.exists())
