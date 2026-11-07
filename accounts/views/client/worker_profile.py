"""Read-only verified worker resume, posts, and client reviews."""
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, render
from accounts.models import SavedWorker
from .access import client_required, discoverable_workers


@client_required
def worker_profile(request, pk):
    profile = get_object_or_404(discoverable_workers(), pk=pk)
    tab = request.GET.get('tab', 'resume')
    if tab not in {'resume', 'posts', 'reviews'}:
        tab = 'resume'
    reviews = profile.client_reviews.select_related('client')
    return render(request, 'clients/worker_profile.html', {
        'profile': profile, 'tab': tab, 'viewing_as_client': True,
        'skill_tags': [s.strip() for s in profile.skills.replace('\n', ',').split(',') if s.strip()],
        'posts': profile.posts.annotate(like_count=Count('likes')),
        'client_reviews': reviews, 'rating': reviews.aggregate(average=Avg('rating'), total=Count('pk')),
        'is_saved': SavedWorker.objects.filter(client=request.user, worker=profile).exists(),
    })
