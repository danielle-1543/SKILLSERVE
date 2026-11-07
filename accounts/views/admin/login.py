"""Compatibility redirect: every account now uses the shared login modal."""
from django.shortcuts import redirect
from django.urls import reverse
from urllib.parse import urlencode


def legacy_admin_login(request):
    next_url = request.GET.get('next', '')
    url = reverse('login')
    if next_url:
        url += '?' + urlencode({'next': next_url})
    return redirect(url)
