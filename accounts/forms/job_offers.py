from django import forms
from django.utils import timezone
from accounts.models import JobOffer, JobComment
from accounts.forms.chat_uploads import MultipleFileField


class JobOfferForm(forms.ModelForm):
    attachments = MultipleFileField(required=False, label='Photos, videos, and files', help_text='Up to 5 files, 25 MB each, 50 MB total. JPG, PNG, WebP, MP4, WebM, PDF, TXT, DOCX, XLSX, PPTX. These are visible to workers viewing your post.')
    class Meta:
        model = JobOffer
        fields = ['title', 'job_type', 'description', 'area', 'scheduled_at', 'preferences', 'budget']
        labels = {'area': 'General location (barangay / city)', 'scheduled_at': 'Date and time', 'budget': 'Proposed budget (PHP, optional)'}
        widgets = {'scheduled_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}), 'description': forms.Textarea(attrs={'rows': 5}), 'preferences': forms.Textarea(attrs={'rows': 3})}
        help_texts = {'area': 'Share a general area only. Discuss your exact address privately.', 'preferences': 'Skills, tools, availability, or other job requirements.', 'description': 'Describe the work without phone numbers, exact addresses, or other private details.'}

    def clean_scheduled_at(self):
        value = self.cleaned_data['scheduled_at']
        if value <= timezone.now():
            raise forms.ValidationError('Choose a future date and time.')
        return value


class JobCommentForm(forms.ModelForm):
    class Meta:
        model = JobComment
        fields = ['body']
        labels = {'body': 'Comment'}
        widgets = {'body': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Ask about the job or introduce your services. Keep contact details private.'})}
