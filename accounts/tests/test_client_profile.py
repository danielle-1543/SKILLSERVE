from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from accounts.models import WorkerProfile, WorkerClientReview, SavedWorker


class ClientProfileTests(TestCase):
    def setUp(self):
        User=get_user_model()
        self.owner=User.objects.create_user(username='profile-client', first_name='Camille', role='client', email='private@example.com')
        self.visitor=User.objects.create_user(username='profile-visitor', role='client')
        worker=User.objects.create_user(username='reviewed-worker',role='worker')
        favorite=User.objects.create_user(username='favorite-worker',role='worker')
        self.reviewed=WorkerProfile.objects.create(user=worker,full_name='Reviewed Worker',status='approved')
        self.favorite=WorkerProfile.objects.create(user=favorite,full_name='Secret Favorite Worker',status='approved')
        WorkerClientReview.objects.create(client=self.owner,profile=self.reviewed,rating=5,feedback='Excellent work and punctual.')
        SavedWorker.objects.create(client=self.owner,worker=self.favorite)

    def test_public_reviews_without_private_favorites_or_contact_data(self):
        url=reverse('public_client_profile',args=[self.owner.pk])
        for user in (None,self.visitor):
            if user:
                self.client.force_login(user)
            response=self.client.get(url)
            self.assertContains(response,'Excellent work and punctual.')
            self.assertNotContains(response,'Secret Favorite Worker')
            self.assertNotContains(response,'private@example.com')
            self.assertNotIn('workers',response.context)
            self.assertEqual(self.client.get(url,{'tab':'saved'}).status_code,404)

    def test_owner_has_private_favorites_and_own_profile(self):
        self.client.force_login(self.owner)
        response=self.client.get(reverse('client_profile'))
        self.assertContains(response,'Your profile')
        self.assertContains(response,'Private')
        response=self.client.get(reverse('client_profile'),{'tab':'saved'})
        self.assertContains(response,'Secret Favorite Worker')
        self.assertContains(response,'Only you can see this list')
        self.assertContains(self.client.get(reverse('saved_workers')),'Secret Favorite Worker')
        self.client.force_login(self.visitor)
        self.assertNotContains(self.client.get(reverse('saved_workers')),'Secret Favorite Worker')

    def test_only_client_profiles_are_public(self):
        self.assertEqual(self.client.get(reverse('public_client_profile',args=[self.reviewed.user_id])).status_code,404)
        self.assertEqual(self.client.get(reverse('client_profile')).status_code,302)
