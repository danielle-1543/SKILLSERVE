"""Shared-login access control for the application administrator role."""
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden


def admin_required(view):
    @login_required(login_url='login')
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_active or not request.user.is_administrator:
            return HttpResponseForbidden('Administrator access is required.')
        return view(request, *args, **kwargs)
    return wrapped
