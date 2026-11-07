from django import forms
from django.contrib.auth.forms import UserCreationForm
from accounts.models import User


class SignUpForm(UserCreationForm):
    role = forms.ChoiceField(choices=[(User.Role.CLIENT, User.Role.CLIENT.label), (User.Role.WORKER, User.Role.WORKER.label)], widget=forms.RadioSelect, label="Choose your account type")
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("role", "first_name", "last_name", "username", "email")

