from django import forms


class WorkerReviewForm(forms.Form):
    revision = forms.IntegerField(widget=forms.HiddenInput)
    decision = forms.ChoiceField(choices=[('approved', 'Approve / verify'), ('rejected', 'Reject'), ('changes', 'Keep pending — request changes')])
    feedback = forms.CharField(max_length=5000, label='Feedback / suggestions / reason', widget=forms.Textarea(attrs={'rows': 5}), help_text='The worker will see this message. Include what to change or the reason for your decision.')
