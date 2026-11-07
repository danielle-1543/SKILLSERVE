"""Client-only access and the verified profiles clients may discover."""
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from accounts.models import WorkerProfile


def client_required(view):
    @login_required(login_url='login')
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if request.user.is_administrator or request.user.role != 'client':
            return HttpResponseForbidden('This feature is for client accounts.')
        return view(request, *args, **kwargs)
    return wrapped


def discoverable_workers():
    return WorkerProfile.objects.filter(status='approved', user__is_active=True, user__role='worker').select_related('user').prefetch_related('services', 'specialties__category', 'specialties__tag')
