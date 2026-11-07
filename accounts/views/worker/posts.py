"""Worker Posts tab: create, remove, and like saved work updates."""
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from accounts.forms.worker_posts import WorkerPostForm
from accounts.models import WorkerProfile, WorkerPost
from .access import worker_required


@worker_required
@require_POST
def manage_worker_post(request):
    profile, _ = WorkerProfile.objects.get_or_create(user=request.user)
    action = request.POST.get('action')
    if action == 'create':
        form = WorkerPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.profile = profile
            post.save()
            messages.success(request, 'Your work update has been posted.')
        else:
            from .dashboard import render_dashboard
            return render_dashboard(request, profile, tab='posts', post_form=form)
    elif action in {'delete', 'like'}:
        post_id = request.POST.get('post_id', '')
        if not post_id.isascii() or not post_id.isdecimal() or len(post_id) > 18:
            from django.http import Http404
            raise Http404
        post = get_object_or_404(WorkerPost, pk=int(post_id), profile=profile)
        if action == 'delete':
            post.delete()
            messages.success(request, 'Work update deleted.')
        elif post.likes.filter(pk=request.user.pk).exists():
            post.likes.remove(request.user)
        else:
            post.likes.add(request.user)
    else:
        messages.error(request, 'Choose a valid post action.')
    return redirect(reverse('worker_profile') + '?tab=posts')
