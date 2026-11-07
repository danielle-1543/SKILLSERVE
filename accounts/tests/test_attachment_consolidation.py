from datetime import timedelta
from django.db import connection, IntegrityError, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase, TestCase
from django.utils import timezone
from accounts.models import Attachment, ChatAttachment, JobAttachment, User, WorkerProfile, Conversation, ChatMessage, JobOffer


class AttachmentOwnershipTests(TestCase):
    def test_database_requires_exactly_one_parent_and_proxies_are_isolated(self):
        client = User.objects.create_user(username='file-client', role='client')
        worker = User.objects.create_user(username='file-worker', role='worker')
        profile = WorkerProfile.objects.create(user=worker)
        thread = Conversation.objects.create(client=client, worker=profile)
        message = ChatMessage.objects.create(conversation=thread, sender=client, body='File')
        offer = JobOffer.objects.create(client=client, scheduled_at=timezone.now()+timedelta(days=1))
        common = {'file':'existing/file.txt', 'name':'file.txt', 'kind':'document'}
        for parents in ({}, {'message': message, 'offer': offer}):
            with self.assertRaises(IntegrityError), transaction.atomic():
                Attachment.objects.create(**common, **parents)
        chat = ChatAttachment.objects.create(message=message, **common)
        job = JobAttachment.objects.create(offer=offer, **common)
        self.assertFalse(JobAttachment.objects.filter(pk=chat.pk).exists())
        self.assertFalse(ChatAttachment.objects.filter(pk=job.pk).exists())
        self.assertEqual(Attachment.objects.count(), 2)
        message.delete()
        self.assertEqual(Attachment.objects.get().pk, job.pk)


class AttachmentMigrationTests(TransactionTestCase):
    old = [('accounts', '0011_jobattachment')]
    new = [('accounts', '0012_consolidate_attachments')]

    def migrate(self, target):
        executor = MigrationExecutor(connection)
        executor.migrate(target)
        return executor.loader.project_state(target).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_merge_and_reverse_preserve_ids_ownership_and_file_paths(self):
        apps = self.migrate(self.old)
        client = apps.get_model('accounts', 'User').objects.create(username='migration-client')
        worker = apps.get_model('accounts', 'User').objects.create(username='migration-worker')
        profile = apps.get_model('accounts', 'WorkerProfile').objects.create(user_id=worker.pk)
        thread = apps.get_model('accounts', 'Conversation').objects.create(client_id=client.pk, worker_id=profile.pk)
        message = apps.get_model('accounts', 'ChatMessage').objects.create(conversation_id=thread.pk, sender_id=client.pk, body='Test')
        offer = apps.get_model('accounts', 'JobOffer').objects.create(client_id=client.pk, scheduled_at=timezone.now())
        apps.get_model('accounts', 'ChatAttachment').objects.create(id=101, message_id=message.pk, file='chat-files/original.pdf', name='chat.pdf', kind='document', size=24)
        apps.get_model('accounts', 'JobAttachment').objects.create(id=202, offer_id=offer.pk, file='job-files/original.jpg', name='job.jpg', kind='image')
        apps = self.migrate(self.new)
        rows = apps.get_model('accounts', 'Attachment').objects
        self.assertEqual(rows.count(), 2)
        self.assertEqual(rows.get(pk=101).message_id, message.pk)
        self.assertEqual(rows.get(pk=101).file.name, 'chat-files/original.pdf')
        self.assertEqual(rows.get(pk=202).offer_id, offer.pk)
        self.assertEqual(rows.get(pk=202).file.name, 'job-files/original.jpg')
        apps = self.migrate(self.old)
        self.assertEqual(apps.get_model('accounts', 'ChatAttachment').objects.get(pk=101).size, 24)
        self.assertEqual(apps.get_model('accounts', 'JobAttachment').objects.get(pk=202).file.name, 'job-files/original.jpg')
