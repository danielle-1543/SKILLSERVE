"""Post composer validation for the worker profile's Posts tab."""
from django import forms
from accounts.models import WorkerPost


class WorkerPostForm(forms.ModelForm):
    class Meta:
        model = WorkerPost
        fields = ['body', 'photo']
        labels = {'body': 'Share an update about your work'}
        widgets = {'body': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Share an update about your work…', 'maxlength': 3000}), 'photo': forms.FileInput(attrs={'accept': 'image/jpeg,image/png,image/webp'})}

    def clean_body(self):
        value = self.cleaned_data['body'].strip()
        return value

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if photo:
            if photo.size > 5 * 1024 * 1024:
                raise forms.ValidationError('Choose an image no larger than 5 MB.')
            if photo.image.format not in {'JPEG', 'PNG', 'WEBP'}:
                raise forms.ValidationError('Choose a JPG, PNG, or WebP image.')
        return photo

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('body') and not cleaned.get('photo'):
            raise forms.ValidationError('Write an update or add a photo before posting.')
        return cleaned
