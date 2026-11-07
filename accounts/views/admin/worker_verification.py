"""Worker submission queue, review decisions, and administrator feedback."""
from django.contrib import messages
from .access import admin_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from accounts.forms.admin import WorkerReviewForm
from accounts.models import WorkerProfile, WorkerReview


@admin_required
def worker_reviews(request):
    status = request.GET.get('status', 'pending')
    profiles = WorkerProfile.objects.exclude(status='draft').select_related('user').order_by('-submitted_at', '-pk')
    if status in dict(WorkerProfile.Status.choices):
        profiles = profiles.filter(status=status)
    else:
        status = 'all'
    return render(request, 'admin_pages/worker_reviews.html', {'page_title': 'Worker verification', 'profiles': profiles, 'selected_status': status, 'statuses': [(value, label) for value, label in WorkerProfile.Status.choices if value != 'draft']})


@admin_required
def review_worker(request, pk):
    profile = get_object_or_404(WorkerProfile.objects.select_related('user'), pk=pk)
    form = WorkerReviewForm(request.POST if request.method == 'POST' else None, initial={'revision': profile.revision})
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            profile = WorkerProfile.objects.select_for_update().get(pk=profile.pk)
            if profile.revision != form.cleaned_data['revision'] or profile.status != WorkerProfile.Status.PENDING:
                form.add_error(None, 'This submission has already changed or been reviewed. Reload the page to see the latest status.')
            else:
                profile.status = form.cleaned_data['decision']
                profile.save(update_fields=['status', 'updated_at'])
                WorkerReview.objects.create(profile=profile, reviewer=request.user, decision=profile.status, feedback=form.cleaned_data['feedback'], revision=profile.revision)
                messages.success(request, 'Decision saved. The worker can now see your feedback.')
                return redirect('review_worker', pk=profile.pk)
    return render(request, 'admin_pages/review_worker.html', {'page_title': 'Review worker profile', 'profile': profile, 'review_form': form, 'reviews': profile.reviews.select_related('reviewer')})
