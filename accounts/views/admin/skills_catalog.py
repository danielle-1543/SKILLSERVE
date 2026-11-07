"""Staff-only category and suggested-specialty management."""
from django.contrib import messages
from .access import admin_required
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from accounts.forms.skills import CategoryForm, TagForm
from accounts.models import SkillCategory, SpecialtyTag


@admin_required
def skills_catalog(request):
    if request.method == 'POST' and request.POST.get('action') not in {'save', 'delete'}:
        return HttpResponseBadRequest('Unsupported catalog action.')
    kind = request.POST.get('kind', request.GET.get('kind', 'category'))
    if kind not in {'category', 'tag'}:
        raise Http404
    model, form_class = (SkillCategory, CategoryForm) if kind == 'category' else (SpecialtyTag, TagForm)
    pk = request.POST.get('entry_id') if request.method == 'POST' else request.GET.get('edit')
    if pk and (not pk.isdecimal() or len(pk) > 18):
        raise Http404
    entry = get_object_or_404(model, pk=pk) if pk else None
    form = form_class(request.POST if request.method == 'POST' else None, instance=entry)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'save' and form.is_valid():
            with transaction.atomic():
                form.save()
            messages.success(request, 'Catalog entry saved.')
            return redirect('skills_catalog')
        elif action == 'delete' and entry:
            try:
                with transaction.atomic():
                    if kind == 'category':
                        entry.tags.all().delete()
                    entry.delete()
                messages.success(request, 'Unused entry deleted.')
            except ProtectedError:
                messages.error(request, 'This entry is used by workers and cannot be deleted. You can edit its name instead.')
            return redirect('skills_catalog')
    return render(request, 'admin_pages/skills_catalog.html', {
        'page_title': 'Skills catalog', 'catalog_form': form, 'kind': kind, 'entry': entry,
        'catalog_categories': SkillCategory.objects.prefetch_related('tags'),
    })
