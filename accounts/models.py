from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Administrator"
        CLIENT = "client", "Client / Employer"
        WORKER = "worker", "Worker / Freelancer"

    # Existing accounts retain an unspecified role until explicitly updated.
    role = models.CharField(max_length=10, choices=Role.choices, blank=True, default="")

    @property
    def is_administrator(self):
        # Retain access for existing staff accounts whose role was never set.
        return self.role == self.Role.ADMIN or self.is_superuser or (self.is_staff and not self.role)


class WorkerProfile(models.Model):
    service_types = models.ManyToManyField("SkillCategory", blank=True, related_name="workers")
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Not submitted'
        PENDING = 'pending', 'Pending review'
        APPROVED = 'approved', 'Verified'
        REJECTED = 'rejected', 'Rejected'
        CHANGES = 'changes', 'Changes requested'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='worker_profile')
    full_name = models.CharField(max_length=180)
    headline = models.CharField(max_length=180, blank=True)
    category = models.CharField(max_length=100)
    location = models.CharField(max_length=180)
    phone = models.CharField(max_length=30)
    availability = models.CharField(max_length=180, blank=True)
    response_time = models.CharField(max_length=100, blank=True)
    service_area = models.CharField(max_length=250, blank=True)
    about = models.TextField(max_length=5000, blank=True)
    skills = models.TextField(max_length=2000)
    certifications = models.TextField(max_length=2000, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    revision = models.PositiveIntegerField(default=0)
    submitted_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)


class WorkerService(models.Model):
    service_type = models.ForeignKey("SkillCategory", null=True, blank=True, on_delete=models.PROTECT, related_name="offered_services")
    profile = models.ForeignKey(WorkerProfile, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=160)
    starting_rate = models.DecimalField(max_digits=10, decimal_places=2)


class WorkerExperience(models.Model):
    profile = models.ForeignKey(WorkerProfile, on_delete=models.CASCADE, related_name='experiences')
    title = models.CharField(max_length=160)
    company = models.CharField(max_length=180)
    years = models.CharField(max_length=80)
    note = models.TextField(max_length=1500, blank=True)


class WorkerEducation(models.Model):
    profile = models.ForeignKey(WorkerProfile, on_delete=models.CASCADE, related_name='education')
    program = models.CharField(max_length=180)
    school = models.CharField(max_length=180)


def evidence_path(instance, filename):
    from pathlib import Path
    from uuid import uuid4
    return f'worker-proofs/{instance.profile_id}/{uuid4().hex}{Path(filename).suffix.lower()}'


def private_storage():
    from django.conf import settings
    from django.core.files.storage import FileSystemStorage
    return FileSystemStorage(location=settings.BASE_DIR / 'private_uploads')


class WorkerEvidence(models.Model):
    profile = models.ForeignKey(WorkerProfile, on_delete=models.CASCADE, related_name='evidence')
    label = models.CharField(max_length=180)
    file = models.FileField(upload_to=evidence_path, storage=private_storage)

    @property
    def preview_type(self):
        from pathlib import Path
        extension = Path(self.file.name).suffix.lower()
        if extension == '.pdf':
            return 'pdf'
        if extension in {'.mp4', '.webm'}:
            return 'video'
        return 'image'


class WorkerReview(models.Model):
    profile = models.ForeignKey(WorkerProfile, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    decision = models.CharField(max_length=12, choices=WorkerProfile.Status.choices)
    feedback = models.TextField(max_length=5000)
    revision = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-pk']

class WorkerPost(models.Model):
    profile = models.ForeignKey(WorkerProfile, on_delete=models.CASCADE, related_name='posts')
    body = models.TextField(max_length=3000, blank=True)
    photo = models.ImageField(upload_to='worker-posts/%Y/%m/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, blank=True, related_name='liked_worker_posts')

    class Meta:
        ordering = ['-created_at', '-pk']


class WorkerClientReview(models.Model):
    profile = models.ForeignKey(WorkerProfile, on_delete=models.CASCADE, related_name='client_reviews')
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='worker_service_reviews')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    feedback = models.TextField(max_length=3000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-pk']

class SavedWorker(models.Model):
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_workers')
    worker = models.ForeignKey(WorkerProfile, on_delete=models.CASCADE, related_name='bookmarks')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['client', 'worker'], name='unique_saved_worker')]


class UserReport(models.Model):
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_reports')
    worker = models.ForeignKey(WorkerProfile, on_delete=models.CASCADE, related_name='user_reports')
    reason = models.CharField(max_length=60)
    details = models.TextField(max_length=3000)
    reviewed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class Conversation(models.Model):
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='client_conversations')
    worker = models.ForeignKey(WorkerProfile, on_delete=models.CASCADE, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['client', 'worker'], name='unique_client_worker_conversation')]


class ChatMessage(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.TextField(max_length=3000)
    created_at = models.DateTimeField(auto_now_add=True)
    reply_to = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies')
    read_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['created_at', 'pk']


class ChatReaction(models.Model):
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    emoji = models.CharField(max_length=10)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['message', 'user'], name='one_reaction_per_user_message')]

def chat_attachment_path(instance, filename):
    from pathlib import Path
    from uuid import uuid4
    return f'chat-files/{instance.message.conversation_id}/{uuid4().hex}{Path(filename).suffix.lower()}'




class Booking(models.Model):
    class Status(models.TextChoices):
        REQUESTED = 'requested', 'Requested'
        ACCEPTED = 'accepted', 'Accepted'
        IN_PROGRESS = 'in_progress', 'In progress'
        AWAITING_CONFIRMATION = 'awaiting_confirmation', 'Awaiting client confirmation'
        COMPLETED = 'completed', 'Completed'
        DECLINED = 'declined', 'Declined'
        CANCELLED = 'cancelled', 'Cancelled'

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='bookings')
    service = models.CharField(max_length=180)
    description = models.TextField(max_length=5000)
    location = models.CharField(max_length=500)
    contact_phone = models.CharField(max_length=30)
    rate = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    rate_basis = models.CharField(max_length=15, choices=[('fixed', 'Fixed total'), ('hour', 'Per hour'), ('day', 'Per day')], default='fixed')
    scheduled_at = models.DateTimeField()
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, validators=[MinValueValidator(0.1)])
    notes = models.TextField(max_length=3000, blank=True)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.REQUESTED)
    revision = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def ticket_number(self):
        return f'SS-{self.pk:06d}'

    class Meta:
        ordering = ['-created_at', '-pk']


class BookingEvent(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='events')
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=24, choices=Booking.Status.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'pk']


class JobOffer(models.Model):
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_offers')
    title = models.CharField(max_length=180)
    job_type = models.CharField(max_length=100)
    description = models.TextField(max_length=4000)
    area = models.CharField(max_length=180)
    scheduled_at = models.DateTimeField()
    preferences = models.TextField(max_length=1500, blank=True)
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(1)])
    is_open = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-pk']


class JobComment(models.Model):
    offer = models.ForeignKey(JobOffer, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.TextField(max_length=1500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'pk']


def job_attachment_path(instance, filename):
    from pathlib import Path
    from uuid import uuid4
    return f'job-files/{instance.offer_id}/{uuid4().hex}{Path(filename).suffix.lower()}'


def attachment_path(instance, filename):
    if instance.message_id:
        return chat_attachment_path(instance, filename)
    return job_attachment_path(instance, filename)


class Attachment(models.Model):
    message = models.ForeignKey(ChatMessage, null=True, blank=True, on_delete=models.CASCADE, related_name='attachments')
    offer = models.ForeignKey(JobOffer, null=True, blank=True, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to=attachment_path, storage=private_storage)
    name = models.CharField(max_length=255)
    kind = models.CharField(max_length=10)
    size = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.CheckConstraint(
            condition=(models.Q(message__isnull=False, offer__isnull=True) | models.Q(message__isnull=True, offer__isnull=False)),
            name='attachment_exactly_one_owner',
        )]


class ChatAttachmentManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(message__isnull=False)


class JobAttachmentManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(offer__isnull=False)


class ChatAttachment(Attachment):
    # Proxy models retain feature-specific APIs without creating extra tables.
    objects = ChatAttachmentManager()

    class Meta:
        proxy = True


class JobAttachment(Attachment):
    objects = JobAttachmentManager()

    class Meta:
        proxy = True


class SkillCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ['name']
        constraints = [models.UniqueConstraint(models.functions.Lower('name'), name='unique_skill_category_name')]

    def __str__(self):
        return self.name


class SpecialtyTag(models.Model):
    category = models.ForeignKey(SkillCategory, on_delete=models.PROTECT, related_name='tags')
    name = models.CharField(max_length=80)

    class Meta:
        ordering = ['name']
        constraints = [models.UniqueConstraint(models.functions.Lower('name'), 'category', name='unique_category_tag')]

    def __str__(self):
        return self.name


class WorkerSpecialty(models.Model):
    profile = models.ForeignKey(WorkerProfile, on_delete=models.CASCADE, related_name='specialties')
    category = models.ForeignKey(SkillCategory, on_delete=models.PROTECT, related_name='worker_specialties')
    tag = models.ForeignKey(SpecialtyTag, null=True, blank=True, on_delete=models.PROTECT, related_name='worker_specialties')
    custom_text = models.CharField(max_length=80, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=(models.Q(tag__isnull=False, custom_text='') | (models.Q(tag__isnull=True) & ~models.Q(custom_text=''))), name='specialty_tag_or_custom'),
            models.UniqueConstraint(fields=['profile', 'tag'], condition=models.Q(tag__isnull=False), name='unique_worker_suggested_tag'),
            models.UniqueConstraint('profile', 'category', models.functions.Lower('custom_text'), condition=models.Q(tag__isnull=True), name='unique_worker_custom_tag'),
        ]

    @property
    def label(self):
        return self.tag.name if self.tag_id else self.custom_text
