"""Client saved-worker list and bookmark toggle."""
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from accounts.models import SavedWorker
from .access import client_required, discoverable_workers


@client_required
@require_POST
def toggle_bookmark(request, pk):
    worker = get_object_or_404(discoverable_workers(), pk=pk)
    saved, created = SavedWorker.objects.get_or_create(client=request.user, worker=worker)
    if not created:
        saved.delete()
    return redirect('client_worker_profile', pk=pk)


@client_required
def saved_workers(request):
    from .profile import render_profile
    return render_profile(request, request.user, tab='saved')
