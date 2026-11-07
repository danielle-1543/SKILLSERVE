from django import forms
from .models import Announcement


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement

        # The author is assigned automatically in the view.
        fields = [
            "title",
            "body",
            "category",
            "photo",
            "is_pinned",
        ]

        labels = {
            "body": "Message",
            "photo": "Photo (optional)",
            "is_pinned": "Pin this announcement",
        }

        widgets = {
            "title": forms.TextInput(
                attrs={"placeholder": "Enter announcement title"}
            ),
            "body": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "Write your announcement",
                }
            ),
            "photo": forms.ClearableFileInput(
                attrs={"accept": "image/jpeg,image/png,image/webp"}
            ),
        }

        help_texts = {
            "photo": "JPG, PNG or WebP. Maximum 5 MB.",
        }

        error_messages = {
            "title": {
                "required": "Please enter a title.",
            },
            "body": {
                "required": "Please enter an announcement message.",
            },
            "photo": {
                "invalid_image": "Please upload a valid image.",
            },
        }

    def clean_photo(self):
        # Check the size and format of newly uploaded images.
        photo = self.cleaned_data.get("photo")

        if not photo:
            return photo

        uploaded_image = getattr(photo, "image", None)

        # Keep an existing image if no replacement was uploaded.
        if uploaded_image is None:
            return photo

        if photo.size > 5 * 1024 * 1024:
            raise forms.ValidationError(
                "Please choose an image no larger than 5 MB."
            )

        if uploaded_image.format not in {"JPEG", "PNG", "WEBP"}:
            raise forms.ValidationError(
                "Please upload a JPG, PNG or WebP image."
            )

        return photo
