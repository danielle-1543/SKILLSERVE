from django.conf import settings
from django.db import models


# Each record in this table represents one announcement.
class Announcement(models.Model):
    # These choices populate the category dropdown.
    class Category(models.TextChoices):
        GENERAL = "general", "General"
        PESO = "peso", "PESO Updates"
        JOB_FAIR = "job_fair", "Job Fairs"
        TRAINING = "training", "Training"
        EMPLOYMENT = "employment", "Employment Information"

    title = models.CharField(max_length=160)
    body = models.TextField()

    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.GENERAL,
    )

    # Images are saved in the media folder.
    # The database stores their file paths.
    photo = models.ImageField(
        upload_to="announcements/%Y/%m/",
        blank=True,
    )

    # Pinned announcements also appear in the pinned panel.
    is_pinned = models.BooleanField(default=False)

    # Link the announcement to the account that created it.
    # PROTECT prevents deleting an author while their posts remain.
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
    )

    # Automatically record when the announcement was created.
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Show the newest announcements first.
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        # Use the title when Django displays this record.
        return self.title