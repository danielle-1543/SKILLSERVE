"""Submit worker-account reports for administrator review."""
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from accounts.forms.client import ReportWorkerForm
from accounts.models import UserReport
from .access import client_required, discoverable_workers


@client_required
def report_worker(request, pk):
    profile = get_object_or_404(discoverable_workers(), pk=pk)
    form = ReportWorkerForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        UserReport.objects.create(reporter=request.user, worker=profile, **form.cleaned_data)
        messages.success(request, 'Your report was sent to the administrators for review.')
        return redirect('client_worker_profile', pk=pk)
    return render(request, 'clients/report_worker.html', {'profile': profile, 'form': form})
