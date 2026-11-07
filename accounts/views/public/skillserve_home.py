"""Public SkillServe introduction and login modal."""
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render


def skillserve_landing(request):
    return render(request, "public/skillserve.html", {"form": AuthenticationForm(request)})
