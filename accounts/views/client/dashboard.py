"""Client dashboard, category shortcuts, and verified-worker search."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from core.models import Announcement


from .categories import service_categories
from django.urls import reverse


@login_required(login_url='login')
def client_dashboard(request):
    if request.user.is_administrator:
        return redirect('admin_dashboard')
    if request.user.role == 'worker':
        return redirect('worker_profile')
    if any(key in request.GET for key in ('q', 'category', 'location')):
        return redirect(reverse('search_workers') + '?' + request.GET.urlencode())
    return render(request, 'clients/dashboard.html', {
        'announcements': Announcement.objects.select_related('author').order_by('-created_at', '-pk')[:3],
        'categories': service_categories(),
    })
