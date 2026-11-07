"""Administrator inbox for reported worker accounts."""
from .access import admin_required
from django.shortcuts import get_object_or_404, redirect, render
from accounts.models import UserReport


@admin_required
def reported_workers(request):
    if request.method == 'POST':
        report = get_object_or_404(UserReport, pk=request.POST.get('report_id'))
        report.reviewed = True
        report.save(update_fields=['reviewed'])
        return redirect('reported_workers')
    return render(request, 'admin_pages/reported_workers.html', {'page_title': 'Reported workers', 'reports': UserReport.objects.select_related('reporter', 'worker').order_by('reviewed', '-created_at')})
