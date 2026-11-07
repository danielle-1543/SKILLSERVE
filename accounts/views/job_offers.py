"""Client job posts and the worker opportunity feed."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404, HttpResponseForbidden, FileResponse
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from accounts.forms.job_offers import JobOfferForm, JobCommentForm
from accounts.models import JobOffer, Conversation, WorkerProfile, JobAttachment
from accounts.forms.chat_uploads import attachment_kind
from accounts.views.client.access import client_required
from accounts.views.worker.access import worker_required


def member_access(request):
    return not request.user.is_administrator and request.user.role in ('client', 'worker')


@login_required
def job_offers(request):
    if not member_access(request):
        return HttpResponseForbidden('Use a client or worker account.')
    offers = JobOffer.objects.filter(client__is_active=True, client__role='client').select_related('client').prefetch_related('comments__author')
    if request.user.role == 'client':
        offers = offers.filter(client=request.user)
    else:
        offers = offers.filter(is_open=True, scheduled_at__gt=timezone.now())
    query = request.GET.get('q', '').strip()[:150]
    if query:
        offers = offers.filter(Q(title__icontains=query) | Q(job_type__icontains=query) | Q(description__icontains=query) | Q(area__icontains=query))
    return render(request, 'jobs/list.html', {'page': Paginator(offers, 12).get_page(request.GET.get('page')), 'query': query, 'now': timezone.now()})


@client_required
def create_job_offer(request):
    form = JobOfferForm(request.POST if request.method == 'POST' else None, request.FILES if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        offer = form.save(commit=False)
        offer.client = request.user
        with transaction.atomic():
            offer.save()
            for file in form.cleaned_data['attachments']:
                JobAttachment.objects.create(offer=offer, file=file, name=file.name[:255], kind=attachment_kind(file.name))
        messages.success(request, 'Your job offer is now visible to workers.')
        return redirect('job_offer_detail', pk=offer.pk)
    return render(request, 'jobs/form.html', {'form': form})


def visible_offer(request, pk):
    offer = get_object_or_404(JobOffer.objects.select_related('client'), pk=pk, client__is_active=True, client__role='client')
    if not member_access(request) or (request.user.role == 'client' and offer.client_id != request.user.pk):
        raise Http404
    return offer


@login_required
def job_offer_detail(request, pk):
    offer = visible_offer(request, pk)
    form = JobCommentForm(request.POST if request.method == 'POST' else None)
    can_comment = offer.is_open and offer.scheduled_at > timezone.now()
    if request.method == 'POST':
        if not can_comment:
            return HttpResponseForbidden('This offer is no longer accepting comments.')
        if form.is_valid():
            comment = form.save(commit=False)
            comment.offer, comment.author = offer, request.user
            comment.save()
            return redirect('job_offer_detail', pk=pk)
    return render(request, 'jobs/detail.html', {'offer': offer, 'comments': offer.comments.select_related('author', 'author__worker_profile'), 'form': form, 'can_comment': can_comment})


@client_required
@require_POST
def close_job_offer(request, pk):
    offer = get_object_or_404(JobOffer, pk=pk, client=request.user)
    offer.is_open = False
    offer.save(update_fields=['is_open'])
    return redirect('job_offer_detail', pk=pk)


@worker_required
@require_POST
def message_job_client(request, pk):
    offer = visible_offer(request, pk)
    if not offer.is_open or offer.scheduled_at <= timezone.now():
        return HttpResponseForbidden('This offer is no longer open.')
    worker = WorkerProfile.objects.filter(user=request.user).first()
    if worker is None:
        messages.info(request, 'Complete your worker profile before messaging clients.')
        return redirect('edit_worker_profile')
    thread, _ = Conversation.objects.get_or_create(client=offer.client, worker=worker)
    return redirect('conversation', pk=thread.pk)


@login_required
def job_attachment(request, pk):
    attachment = get_object_or_404(JobAttachment, pk=pk)
    visible_offer(request, attachment.offer_id)
    import mimetypes
    content_type = mimetypes.guess_type(attachment.name)[0] or 'application/octet-stream'
    response = FileResponse(attachment.file.open('rb'), content_type=content_type, filename=attachment.name, as_attachment=attachment.kind == 'document')
    response['X-Content-Type-Options'] = 'nosniff'
    response['Cache-Control'] = 'private, no-store'
    return response
