"""Worker dashboard: resume, work updates, client reviews, and private review status."""
from django.db.models import Avg, Count
from django.shortcuts import render
from accounts.forms.worker_posts import WorkerPostForm
from accounts.models import WorkerProfile, JobOffer, Booking
from django.utils import timezone
from .access import worker_required


def render_dashboard(request, profile, tab='resume', post_form=None):
    client_reviews = profile.client_reviews.select_related('client')
    rating = client_reviews.aggregate(average=Avg('rating'), total=Count('pk'))
    skills = [skill.strip() for skill in profile.skills.replace('\n', ',').split(',') if skill.strip()]
    posts = profile.posts.annotate(like_count=Count('likes')).prefetch_related('likes')
    liked_ids = set(request.user.liked_worker_posts.filter(profile=profile).values_list('pk', flat=True))
    return render(request, 'workers/profile.html', {
        'profile': profile, 'tab': tab,
        'open_job_count': JobOffer.objects.filter(is_open=True, scheduled_at__gt=timezone.now(), client__is_active=True, client__role='client').count(),
        'active_booking_count': Booking.objects.filter(conversation__worker=profile, status__in=['requested', 'accepted', 'in_progress', 'awaiting_confirmation']).count(),
        'service_count': profile.services.count(),
        'reviews': profile.reviews.select_related('reviewer'),
        'latest_review': profile.reviews.first(),
        'client_reviews': client_reviews, 'rating': rating,
        'skill_tags': skills, 'posts': posts, 'liked_ids': liked_ids,
        'post_form': post_form if post_form is not None else WorkerPostForm(),
        'other_workers': WorkerProfile.objects.filter(status='approved').exclude(pk=profile.pk).select_related('user')[:3],
    })


@worker_required
def worker_dashboard(request):
    profile, _ = WorkerProfile.objects.get_or_create(user=request.user)
    tab = request.GET.get('tab', 'resume')
    if tab not in {'resume', 'posts', 'reviews'}:
        tab = 'resume'
    return render_dashboard(request, profile, tab)
