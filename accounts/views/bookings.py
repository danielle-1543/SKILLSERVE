"""Create booking tickets and enforce role-specific status transitions."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from accounts.forms.booking import BookingForm
from accounts.models import Booking, BookingEvent
from accounts.views.client.access import client_required
from .messaging import participant_thread, render_conversation


@client_required
@require_POST
def request_booking(request, pk):
    thread = participant_thread(request.user, pk)
    if thread.client_id != request.user.pk or thread.worker.status != 'approved' or not thread.worker.user.is_active:
        raise Http404
    form = BookingForm(request.POST)
    if form.is_valid():
        with transaction.atomic():
            booking = form.save(commit=False)
            booking.conversation = thread
            booking.save()
            BookingEvent.objects.create(booking=booking, actor=request.user, status='requested')
        messages.success(request, f'Booking {booking.ticket_number} requested. Waiting for the worker to accept.')
        return redirect('conversation', pk=pk)
    return render_conversation(request, thread, booking_form=form, open_booking=True)


@login_required(login_url='login')
@require_POST
def update_booking(request, pk):
    with transaction.atomic():
        booking = get_object_or_404(Booking.objects.select_for_update().select_related('conversation__worker'), pk=pk)
        thread = participant_thread(request.user, booking.conversation_id)
        worker_actions = {'accept': ('requested', 'accepted'), 'decline': ('requested', 'declined'), 'start': ('accepted', 'in_progress'), 'finish': ('in_progress', 'awaiting_confirmation')}
        client_actions = {'confirm': ('awaiting_confirmation', 'completed')}
        action = request.POST.get('action')
        allowed = worker_actions if request.user.pk == thread.worker.user_id else client_actions
        if action == 'cancel' and request.user.pk == thread.client_id and booking.status in {'requested','accepted'}:
            target = 'cancelled'
        elif action in allowed and allowed[action][0] == booking.status:
            target = allowed[action][1]
        else:
            messages.error(request, 'That action is not available for this booking status.')
            return redirect('conversation', pk=thread.pk)
        if request.POST.get('revision') != str(booking.revision):
            messages.error(request, 'The booking changed. Review the latest status before trying again.')
            return redirect('conversation', pk=thread.pk)
        booking.status = target
        booking.revision += 1
        booking.save(update_fields=['status','revision','updated_at'])
        BookingEvent.objects.create(booking=booking, actor=request.user, status=target)
    messages.success(request, f'{booking.ticket_number}: {booking.get_status_display()}.')
    return redirect('conversation', pk=thread.pk)
