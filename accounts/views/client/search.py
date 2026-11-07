"""Dedicated paginated worker search results."""
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from .access import client_required, discoverable_workers
from .categories import service_categories


@client_required
def search_workers(request):
    query = request.GET.get('q', '').strip()[:150]
    location = request.GET.get('location', '').strip()[:150]
    category = request.GET.get('category', '')
    selected = next((item for item in service_categories() if item['slug'] == category), None)
    workers = discoverable_workers()
    if query:
        # Match names in either order, extra spaces, and account usernames.
        for term in query.split():
            workers = workers.filter(
                Q(full_name__icontains=term) | Q(user__username__icontains=term)
                | Q(user__first_name__icontains=term) | Q(user__last_name__icontains=term)
                | Q(headline__icontains=term) | Q(skills__icontains=term)
                | Q(category__icontains=term) | Q(services__name__icontains=term)
                | Q(specialties__category__name__icontains=term) | Q(specialties__tag__name__icontains=term) | Q(specialties__custom_text__icontains=term)
            )
    if location:
        workers = workers.filter(Q(location__icontains=location) | Q(service_area__icontains=location))
    if selected:
        condition = Q(specialties__category__slug=selected['slug'])
        for term in selected['terms']:
            condition |= Q(category__icontains=term) | Q(services__name__icontains=term) | Q(skills__icontains=term)
        workers = workers.filter(condition)
    workers = workers.distinct().order_by('full_name', 'pk')
    page = Paginator(workers, 12).get_page(request.GET.get('page'))
    filters = request.GET.copy()
    filters.pop('page', None)
    return render(request, 'clients/search.html', {
        'categories': service_categories(), 'query': query, 'location': location,
        'selected_category': selected, 'workers': page, 'page_obj': page,
        'worker_count': page.paginator.count, 'filter_query': filters.urlencode(),
    })
