"""Authenticated private inline proof previews for owners and administrators."""
from django.contrib.auth.decorators import login_required
from pathlib import Path
from django.http import FileResponse, Http404
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.shortcuts import get_object_or_404
from accounts.models import WorkerEvidence


@xframe_options_sameorigin
@login_required(login_url='login')
def worker_evidence(request, pk):
    evidence = get_object_or_404(WorkerEvidence.objects.select_related('profile'), pk=pk)
    if not request.user.is_administrator and evidence.profile.user_id != request.user.pk:
        raise Http404
    try:
        response = FileResponse(evidence.file.open('rb'), as_attachment=False, content_type={'.pdf': 'application/pdf', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp', '.mp4': 'video/mp4', '.webm': 'video/webm'}.get(Path(evidence.file.name).suffix.lower(), 'application/octet-stream'), filename=evidence.file.name.rsplit('/', 1)[-1])
    except FileNotFoundError:
        raise Http404('This file is unavailable.')
    response['X-Content-Type-Options'] = 'nosniff'
    response['Cache-Control'] = 'private, no-store'
    return response
