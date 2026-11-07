"""Shared worker-only access guard."""
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from accounts.models import User


def worker_required(view):
    @login_required(login_url='login')
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if request.user.is_administrator:
            return redirect('admin_dashboard')
        if request.user.role != User.Role.WORKER:
            return HttpResponseForbidden('This page is for worker accounts.')
        return view(request, *args, **kwargs)
    return wrapped
