"""Client profiles: public authored reviews and owner-only saved workers."""
from django.shortcuts import get_object_or_404, render
from accounts.models import User
from .access import client_required, discoverable_workers


def render_profile(request, account, tab=None):
    is_owner = request.user.is_authenticated and request.user.pk == account.pk
    selected = tab or request.GET.get('tab', 'reviews')
    if selected == 'saved' and not is_owner:
        from django.http import Http404
        raise Http404
    if selected not in {'reviews', 'saved'}:
        selected = 'reviews'
    context = {
        'account': account, 'is_owner': is_owner, 'tab': selected,
        'authored_reviews': account.worker_service_reviews.select_related('profile__user').order_by('-created_at', '-pk'),
    }
    # Do not query or include private favorites for any other visitor.
    if is_owner:
        context['workers'] = discoverable_workers().filter(bookmarks__client=account).order_by('full_name')
    return render(request, 'clients/profile.html', context)


@client_required
def my_profile(request):
    return render_profile(request, request.user)


def public_profile(request, pk):
    account = get_object_or_404(User, pk=pk, role='client', is_active=True)
    return render_profile(request, account)
