"""Private Messenger-style conversations and participant-only chat actions."""
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Max, Count
from django.db import transaction
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST
from accounts.forms.client import MessageForm
from accounts.models import Conversation, ChatMessage, ChatReaction, ChatAttachment
from accounts.views.client.access import client_required, discoverable_workers


def participant_thread(user, pk):
    return get_object_or_404(Conversation.objects.filter(Q(client=user) | Q(worker__user=user)).select_related('client', 'worker__user'), pk=pk)


def threads_for(user):
    return Conversation.objects.filter(Q(client=user) | Q(worker__user=user)).select_related('client', 'worker__user').annotate(latest=Max('messages__created_at'), unread=Count('messages', filter=Q(messages__read_at__isnull=True, messages__deleted_at__isnull=True) & ~Q(messages__sender=user))).prefetch_related('messages').order_by('-latest', '-created_at')


def chat_context(request, thread):
    thread.messages.exclude(sender=request.user).filter(read_at__isnull=True).update(read_at=timezone.now())
    chat = thread.messages.select_related('sender', 'reply_to').prefetch_related('reactions', 'attachments')
    return {'thread': thread, 'chat': chat, 'other_user': thread.worker.user if thread.client_id == request.user.pk else thread.client, 'is_client': thread.client_id == request.user.pk, 'bookings': thread.bookings.prefetch_related('events__actor')}


@client_required
@require_POST
def start_conversation(request, pk):
    worker = get_object_or_404(discoverable_workers(), pk=pk)
    thread, _ = Conversation.objects.get_or_create(client=request.user, worker=worker)
    return redirect('conversation', pk=thread.pk)


@login_required(login_url='login')
def inbox(request):
    return render(request, 'messages/inbox.html', {'threads': threads_for(request.user)})


@login_required(login_url='login')
def conversation(request, pk):
    thread = participant_thread(request.user, pk)
    form = MessageForm(request.POST if request.method == 'POST' else None, request.FILES if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        reply = None
        reply_id = request.POST.get('reply_to', '')
        if reply_id:
            if not reply_id.isdecimal() or len(reply_id) > 18:
                raise Http404
            reply = get_object_or_404(ChatMessage, pk=int(reply_id), conversation=thread, deleted_at__isnull=True)
        from accounts.forms.chat_uploads import attachment_kind
        with transaction.atomic():
            message = ChatMessage.objects.create(conversation=thread, sender=request.user, body=form.cleaned_data['body'], reply_to=reply)
            for file in form.cleaned_data['attachments']:
                ChatAttachment.objects.create(message=message, file=file, name=file.name[:255], kind=attachment_kind(file.name), size=file.size)
        return redirect('conversation', pk=pk)
    return render_conversation(request, thread, message_form=form)


def render_conversation(request, thread, message_form=None, booking_form=None, open_booking=False):
    from accounts.forms.booking import BookingForm
    context = chat_context(request, thread)
    context.update(form=message_form if message_form is not None else MessageForm(), threads=threads_for(request.user), booking_form=booking_form if booking_form is not None else BookingForm(), open_booking=open_booking)
    return render(request, 'messages/conversation.html', context)


@login_required(login_url='login')
def chat_updates(request, pk):
    import hashlib
    thread = participant_thread(request.user, pk)
    context = chat_context(request, thread)
    state = [(m.pk, str(m.deleted_at), str(m.read_at), [(r.user_id, r.emoji) for r in m.reactions.all()]) for m in context['chat']]
    signature = hashlib.sha256(repr(state).encode()).hexdigest()
    booking_state = [(b.pk, b.revision) for b in context['bookings']]
    response = JsonResponse({'booking_signature': repr(booking_state), 'booking_html': render_to_string('messages/booking_tickets.html', context, request=request), 'html': render_to_string('messages/message_list.html', context, request=request), 'signature': signature})
    response['Cache-Control'] = 'private, no-store'
    return response


@login_required(login_url='login')
@require_POST
def message_action(request, pk, message_id):
    thread = participant_thread(request.user, pk)
    message = get_object_or_404(ChatMessage, conversation=thread, pk=message_id)
    action = request.POST.get('action')
    if action == 'unsend':
        if message.sender_id != request.user.pk:
            raise Http404
        message.body = ''
        message.deleted_at = timezone.now()
        message.save(update_fields=['body', 'deleted_at'])
        message.reactions.all().delete()
    elif action == 'react' and message.deleted_at is None:
        emoji = request.POST.get('emoji')
        if emoji in ['👍', '❤️', '😊', '🎉']:
            reaction, created = ChatReaction.objects.get_or_create(message=message, user=request.user, defaults={'emoji': emoji})
            if not created:
                if reaction.emoji == emoji:
                    reaction.delete()
                else:
                    reaction.emoji = emoji
                    reaction.save(update_fields=['emoji'])
    return redirect('conversation', pk=pk)
