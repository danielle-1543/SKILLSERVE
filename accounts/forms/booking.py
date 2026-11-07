"""Structured booking-ticket fields, ready for future export and AI assistance."""
from django import forms
from django.utils import timezone
from accounts.models import Booking


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['service', 'description', 'location', 'contact_phone', 'rate', 'rate_basis', 'scheduled_at', 'estimated_hours', 'notes']
        labels = {'service': 'Type of service', 'description': 'Job description / work required', 'location': 'Full job location / address', 'rate': 'Proposed rate (PHP)', 'scheduled_at': 'Date and time (Philippine time)', 'estimated_hours': 'Estimated duration (hours)', 'notes': 'Special instructions / materials / access details'}
        widgets = {'scheduled_at': forms.DateTimeInput(attrs={'type':'datetime-local'}, format='%Y-%m-%dT%H:%M'), 'description': forms.Textarea(attrs={'rows':3}), 'notes': forms.Textarea(attrs={'rows':2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, placeholder in {
            'service': 'e.g. Kitchen sink repair',
            'description': 'Describe the work and the result you need.',
            'location': 'House / building, street, barangay, and city',
            'contact_phone': 'e.g. 0917 123 4567',
            'rate': '0.00',
            'estimated_hours': 'Optional',
            'notes': 'Tools, materials, access instructions… (optional)',
        }.items():
            self.fields[name].widget.attrs['placeholder'] = placeholder
        self.fields['contact_phone'].widget.attrs['autocomplete'] = 'tel'
        self.fields['contact_phone'].widget.attrs['inputmode'] = 'tel'

    def clean_scheduled_at(self):
        date = self.cleaned_data['scheduled_at']
        if date <= timezone.now():
            raise forms.ValidationError('Choose a future date and time.')
        return date

    def clean_contact_phone(self):
        value = self.cleaned_data['contact_phone']
        if sum(c.isdigit() for c in value) < 7 or any(c not in '+()- .0123456789' for c in value):
            raise forms.ValidationError('Enter a valid contact phone number.')
        return value
