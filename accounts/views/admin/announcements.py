
from django.contrib import messages
from .access import admin_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date
from core.models import Announcement
from core.forms import AnnouncementForm


@admin_required
def CRUD_annoucements(request):
    # Prefixes give Create and Edit forms different HTML field IDs.
    create_form = AnnouncementForm(prefix="create")

    invalid_edit_form = None
    invalid_edit_id = None
    open_modal = ""

    if request.method == "POST":
        # Each modal sends a hidden action: create, edit, or delete.
        action = request.POST.get("action")

        if action == "create":
            create_form = AnnouncementForm(
                request.POST,
                request.FILES,
                prefix="create",
            )

            if create_form.is_valid():
                # Assign the signed-in admin as the author before saving.
                announcement = create_form.save(commit=False)
                announcement.author = request.user
                announcement.save()

                messages.success(request, "Announcement published.")
                return redirect("CRUD_annoucements")

            # Reopen the modal so the admin can correct the form errors.
            open_modal = "create-modal"

        elif action in {"edit", "delete", "pin"}:
            announcement_id = request.POST.get("announcement_id", "")

            # Accept only a positive numeric record ID.
            if (
                not announcement_id.isascii()
                or not announcement_id.isdecimal()
                or len(announcement_id) > 19
            ):
                messages.error(
                    request,
                    "Please select a valid announcement.",
                )
                return redirect("CRUD_annoucements")

            announcement_id = int(announcement_id)

            if not 1 <= announcement_id <= 9223372036854775807:
                messages.error(
                    request,
                    "Please select a valid announcement.",
                )
                return redirect("CRUD_annoucements")

            announcement = get_object_or_404(
                Announcement,
                pk=announcement_id,
            )

            if action == "pin":
                announcement.is_pinned = not announcement.is_pinned
                announcement.save(update_fields=["is_pinned"])
                messages.success(request, "Pinned announcements updated.")
                return redirect("CRUD_annoucements")

            if action == "delete":
                # Delete only after the confirmation modal submits.
                announcement.delete()

                messages.success(request, "Announcement deleted.")
                return redirect("CRUD_annoucements")

            # Update the selected record while keeping its original author.
            edit_form = AnnouncementForm(
                request.POST,
                request.FILES,
                instance=announcement,
                prefix=f"edit-{announcement.pk}",
            )

            if edit_form.is_valid():
                edit_form.save()

                messages.success(request, "Announcement updated.")
                return redirect("CRUD_annoucements")

            # Keep the submitted values and show errors in the same modal.
            invalid_edit_form = edit_form
            invalid_edit_id = announcement.pk
            open_modal = f"edit-modal-{announcement.pk}"

        else:
            messages.error(request, "Please choose a valid action.")
            return redirect("CRUD_annoucements")

    # Load actual announcements and prepare each card's edit form.
    announcements = (
        Announcement.objects.select_related("author")
        .order_by("-created_at", "-pk")
    )
    announcement_rows = []

    all_posts = Announcement.objects.select_related("author")
    category = request.GET.get("category", "")
    if category in dict(Announcement.Category.choices):
        announcements = announcements.filter(category=category)
    else:
        category = ""
    def filter_date(value):
        try:
            return parse_date(value)
        except ValueError:
            return None

    start = filter_date(request.GET.get("start", ""))
    end = filter_date(request.GET.get("end", ""))
    if start:
        announcements = announcements.filter(created_at__date__gte=start)
    if end:
        announcements = announcements.filter(created_at__date__lte=end)
    sort = request.GET.get("sort", "newest")
    if sort == "oldest":
        announcements = announcements.order_by("created_at", "pk")
    counts = dict(all_posts.values("category").annotate(total=Count("pk")).values_list("category", "total"))

    # Include full-post dialogs for pinned items outside the filtered feed.
    pinned_posts = list(all_posts.filter(is_pinned=True)[:4])
    visible_ids = set(announcements.values_list("pk", flat=True))

    for announcement in announcements:
        if announcement.pk == invalid_edit_id:
            edit_form = invalid_edit_form
        else:
            edit_form = AnnouncementForm(
                instance=announcement,
                prefix=f"edit-{announcement.pk}",
            )

        announcement_rows.append(
            {
                "post": announcement,
                "edit_form": edit_form,
            }
        )

    # Render one page containing the feed and all announcement modals.
    return render(
        request,
        "admin_pages/CRUD_annoucements.html",
        {
            "page_title": "Announcements",
            "create_form": create_form,
            "announcement_rows": announcement_rows,
            "pinned_posts": pinned_posts,
            "extra_pinned_posts": [post for post in pinned_posts if post.pk not in visible_ids],
            "categories": [{"value": value, "label": label, "count": counts.get(value, 0)} for value, label in Announcement.Category.choices],
            "selected_category": category,
            "total_posts": all_posts.count(),
            "selected_sort": sort,
            "start_date": request.GET.get("start", ""),
            "end_date": request.GET.get("end", ""),
            "open_modal": open_modal,
        },
    )
