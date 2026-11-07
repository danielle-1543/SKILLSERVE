"""Worker profile editing, service rows, proof uploads, and submission."""
from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone
from accounts.models import WorkerProfile, SkillCategory
from accounts.forms.worker import WorkerProfileForm, ServiceFormSet, ExperienceFormSet, EducationFormSet, EvidenceFormSet
from .access import worker_required


@worker_required
def edit_worker_profile(request):
    profile, _ = WorkerProfile.objects.get_or_create(user=request.user, defaults={'full_name': request.user.get_full_name()})
    data = request.POST if request.method == 'POST' else None
    files = request.FILES if request.method == 'POST' else None
    form = WorkerProfileForm(data, instance=profile)
    if data is not None:
        selected_ids = data.getlist('service_types')
    else:
        selected_ids = list(profile.service_types.values_list('pk', flat=True))
    selected_types = SkillCategory.objects.filter(pk__in=[int(x) for x in selected_ids if str(x).isdigit()])
    sections = [
        {'title': 'Services Offered and starting rates', 'prefix': 'services', 'add_label': 'Add service', 'formset': ServiceFormSet(data, instance=profile, prefix='services', form_kwargs={'service_types': selected_types})},
        {'title': 'Work experience', 'prefix': 'experience', 'add_label': 'Add experience', 'formset': ExperienceFormSet(data, instance=profile, prefix='experience')},
        {'title': 'Education and training', 'prefix': 'education', 'add_label': 'Add education / training', 'formset': EducationFormSet(data, instance=profile, prefix='education')},
        {'title': 'Proof and certifications', 'prefix': 'evidence', 'add_label': 'Add proof / file', 'formset': EvidenceFormSet(data, files, instance=profile, prefix='evidence')},
    ]
    if request.method == 'POST':
        valid = form.is_valid()
        for section in sections:
            valid = section['formset'].is_valid() and valid
        if valid:
            with transaction.atomic():
                current = WorkerProfile.objects.select_for_update().get(pk=profile.pk)
                if request.POST.get('revision') != str(current.revision):
                    form.add_error(None, 'This profile changed in another tab. Reload the page before submitting again.')
                else:
                    profile = form.save(commit=False)
                    category_ids = [category.pk for category in form.cleaned_data['service_types']]
                    profile.category = ', '.join(SkillCategory.objects.filter(pk__in=category_ids).values_list('name', flat=True))[:100]
                    profile.status = WorkerProfile.Status.PENDING
                    profile.revision = current.revision + 1
                    profile.submitted_at = timezone.now()
                    profile.save()
                    form.save_m2m()
                    for section in sections:
                        section['formset'].save()
                    messages.success(request, 'Profile submitted for administrator review. You can track the decision and feedback here.')
                    return redirect('worker_profile')
        messages.error(request, 'Please correct the highlighted fields. If you selected new files, select them again before resubmitting.')
    return render(request, 'workers/edit_profile.html', {'profile': profile, 'form': form, 'sections': sections, 'reviews': profile.reviews.all()[:1]})
