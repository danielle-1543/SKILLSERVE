from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from accounts.models import WorkerProfile, Conversation, ChatMessage, ChatReaction


class MessengerTests(TestCase):
    def setUp(self):
        User=get_user_model()
        self.client_user=User.objects.create_user(username='messenger-client', role='client')
        self.worker=User.objects.create_user(username='messenger-worker', first_name='Daniela', role='worker')
        self.stranger=User.objects.create_user(username='messenger-stranger', role='client')
        profile=WorkerProfile.objects.create(user=self.worker, full_name='Daniela Worker', status='approved')
        self.thread=Conversation.objects.create(client=self.client_user, worker=profile)
        self.message=ChatMessage.objects.create(conversation=self.thread, sender=self.worker, body='How can I help?')
        self.client.force_login(self.client_user)

    def test_messenger_layout_avatar_seen_and_polling(self):
        response=self.client.get(reverse('conversation', args=[self.thread.pk]))
        self.assertContains(response, 'worker-avatar-badge')
        self.assertContains(response, 'messenger-sidebar')
        self.assertContains(response, 'Search conversations')
        self.message.refresh_from_db()
        self.assertIsNotNone(self.message.read_at)
        response=self.client.get(reverse('chat_updates', args=[self.thread.pk]))
        self.assertContains(response, 'How can I help?')
        self.client.force_login(self.stranger)
        self.assertEqual(self.client.get(reverse('chat_updates', args=[self.thread.pk])).status_code,404)

    def test_replies_and_reactions(self):
        url=reverse('conversation', args=[self.thread.pk])
        self.client.post(url, {'body':'Please repair the pipe.', 'reply_to':self.message.pk})
        reply=ChatMessage.objects.exclude(pk=self.message.pk).get()
        self.assertEqual(reply.reply_to_id,self.message.pk)
        action=reverse('message_action', args=[self.thread.pk,self.message.pk])
        self.client.post(action, {'action':'react','emoji':'👍'})
        self.assertEqual(ChatReaction.objects.get().emoji,'👍')
        self.client.post(action, {'action':'react','emoji':'👍'})
        self.assertFalse(ChatReaction.objects.exists())

    def test_unsend_own_message_only(self):
        action=reverse('message_action', args=[self.thread.pk,self.message.pk])
        self.assertEqual(self.client.post(action, {'action':'unsend'}).status_code,404)
        self.client.force_login(self.worker)
        self.client.post(action, {'action':'unsend'})
        self.message.refresh_from_db()
        self.assertIsNotNone(self.message.deleted_at)
        self.assertEqual(self.message.body,'')
        self.assertContains(self.client.get(reverse('conversation', args=[self.thread.pk])), 'This message was unsent.')
