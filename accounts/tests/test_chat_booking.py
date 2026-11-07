from datetime import timedelta
from io import BytesIO
from django.contrib.auth import get_user_model
from django.core.files.storage import InMemoryStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from accounts.models import WorkerProfile, Conversation, ChatMessage, ChatAttachment, Booking, BookingEvent


class ChatAttachmentBookingTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.customer = User.objects.create_user(username='booking-client', role='client')
        self.worker = User.objects.create_user(username='booking-worker', role='worker')
        self.stranger = User.objects.create_user(username='booking-stranger', role='client')
        self.profile = WorkerProfile.objects.create(user=self.worker, full_name='Skilled Worker', status='approved')
        self.thread = Conversation.objects.create(client=self.customer, worker=self.profile)
        self.client.force_login(self.customer)
        field = ChatAttachment._meta.get_field('file')
        original = field.storage
        field.storage = InMemoryStorage()
        self.addCleanup(setattr, field, 'storage', original)

    def payload(self):
        return {'service':'Pipe repair', 'description':'Replace leaking kitchen pipe', 'location':'123 Sample Street', 'contact_phone':'09171234567', 'rate':'500', 'rate_basis':'fixed', 'scheduled_at':timezone.localtime(timezone.now()+timedelta(days=2)).strftime('%Y-%m-%dT%H:%M'), 'estimated_hours':'2', 'notes':'Bring pipe fittings'}

    def book(self):
        response = self.client.post(reverse('request_booking', args=[self.thread.pk]), self.payload())
        self.assertRedirects(response, reverse('conversation', args=[self.thread.pk]))
        return Booking.objects.get()

    def test_booking_request_default_status_and_full_lifecycle(self):
        booking = self.book()
        self.assertEqual(booking.status,'requested')
        self.assertEqual(booking.location,'123 Sample Street')
        self.assertEqual(BookingEvent.objects.count(),1)
        self.client.force_login(self.worker)
        for action, expected in [('accept','accepted'),('start','in_progress'),('finish','awaiting_confirmation')]:
            self.client.post(reverse('update_booking', args=[booking.pk]), {'action':action,'revision':booking.revision})
            booking.refresh_from_db()
            self.assertEqual(booking.status,expected)
        self.client.force_login(self.customer)
        self.client.post(reverse('update_booking', args=[booking.pk]), {'action':'confirm','revision':booking.revision})
        booking.refresh_from_db()
        self.assertEqual(booking.status,'completed')
        self.assertEqual(booking.events.count(),5)

    def test_booking_invalid_dates_rates_and_roles(self):
        data = self.payload()
        data.update(rate='-10',scheduled_at='2020-01-01T12:00')
        response = self.client.post(reverse('request_booking', args=[self.thread.pk]), data)
        self.assertTrue(response.context['booking_form'].errors)
        self.assertTrue(response.context['open_booking'])
        self.assertFalse(Booking.objects.exists())
        booking = self.book()
        self.client.post(reverse('update_booking',args=[booking.pk]), {'action':'accept','revision':0})
        booking.refresh_from_db()
        self.assertEqual(booking.status,'requested')
        self.client.force_login(self.stranger)
        self.assertEqual(self.client.post(reverse('update_booking',args=[booking.pk]), {'action':'cancel','revision':0}).status_code,404)
        self.client.force_login(self.worker)
        self.assertEqual(self.client.post(reverse('request_booking',args=[self.thread.pk]),data).status_code,403)
        self.client.post(reverse('update_booking',args=[booking.pk]), {'action':'accept','revision':99})
        booking.refresh_from_db()
        self.assertEqual(booking.status,'requested')

    def test_decline_and_cancel(self):
        booking = self.book()
        self.client.force_login(self.worker)
        self.client.post(reverse('update_booking',args=[booking.pk]), {'action':'decline','revision':0})
        booking.refresh_from_db()
        self.assertEqual(booking.status,'declined')
        self.client.force_login(self.customer)
        self.client.post(reverse('request_booking',args=[self.thread.pk]),self.payload())
        another = Booking.objects.exclude(pk=booking.pk).get()
        self.client.post(reverse('update_booking',args=[another.pk]), {'action':'cancel','revision':0})
        another.refresh_from_db()
        self.assertEqual(another.status,'cancelled')

    def test_send_image_document_video_and_private_preview(self):
        data = BytesIO()
        Image.new('RGB',(10,10),'red').save(data,format='PNG')
        files = [SimpleUploadedFile('image.png',data.getvalue(),'image/png'),SimpleUploadedFile('details.pdf',b'%PDF-1.4\nExample','application/pdf'),SimpleUploadedFile('clip.mp4',b'\x00\x00\x00\x18ftypmp42'+b'0'*80,'video/mp4')]
        response=self.client.post(reverse('conversation',args=[self.thread.pk]),{'body':'','attachments':files})
        self.assertRedirects(response,reverse('conversation',args=[self.thread.pk]))
        self.assertEqual(ChatAttachment.objects.count(),3)
        video=ChatAttachment.objects.get(kind='video')
        url=reverse('chat_attachment',args=[video.pk])
        response=self.client.get(url,HTTP_RANGE='bytes=0-9')
        self.assertEqual(response.status_code,206)
        self.assertEqual(len(b''.join(response.streaming_content)),10)
        response.close()
        self.client.force_login(self.stranger)
        self.assertEqual(self.client.get(url).status_code,404)
        self.client.force_login(self.worker)
        response=self.client.get(url)
        self.assertEqual(response.status_code,200)
        response.close()
        self.client.force_login(self.customer)
        message=ChatMessage.objects.get()
        self.client.post(reverse('message_action',args=[self.thread.pk,message.pk]),{'action':'unsend'})
        self.assertEqual(self.client.get(url).status_code,404)

    def test_invalid_uploads_do_not_send_and_updates_include_booking(self):
        response=self.client.post(reverse('conversation',args=[self.thread.pk]),{'body':'Test','attachments':[SimpleUploadedFile('bad.exe',b'data')]})
        self.assertTrue(response.context['form'].errors)
        self.assertFalse(ChatMessage.objects.exists())
        booking=self.book()
        response=self.client.get(reverse('chat_updates',args=[self.thread.pk]))
        self.assertIn(booking.ticket_number,response.json()['booking_html'])
        self.assertIn('Requested',response.json()['booking_html'])
