"""Forms for contacting workers and reporting an account."""
from django import forms
from .chat_uploads import MultipleFileField, MultipleFileInput


class MessageForm(forms.Form):
    body = forms.CharField(max_length=3000, strip=True, required=False, label='Message', widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Write your message…'}))
    attachments = MultipleFileField(required=False, widget=MultipleFileInput(attrs={'accept': '.jpg,.jpeg,.png,.webp,.pdf,.txt,.docx,.xlsx,.pptx,.mp4,.webm'}))

    def clean(self):
        data = super().clean()
        if not data.get('body') and not data.get('attachments'):
            raise forms.ValidationError('Write a message or attach a file.')
        return data


class ReportWorkerForm(forms.Form):
    reason = forms.ChoiceField(choices=[('misleading', 'Misleading profile or information'), ('harassment', 'Harassment or inappropriate behavior'), ('scam', 'Suspected scam'), ('other', 'Other')])
    details = forms.CharField(max_length=3000, strip=True, label='What happened?', widget=forms.Textarea(attrs={'rows': 5}))
