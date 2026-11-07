"""Administrator dashboard."""
from .access import admin_required
from django.shortcuts import render
from core.models import Announcement


@admin_required
def admin_dashboard(request):
    # Display the five most recent announcements from the database.
    recent_announcements = (
        Announcement.objects.select_related("author")
        .order_by("-created_at", "-pk")[:5]
    )

    return render(
        request,
        "admin_pages/admin_dashboard.html",
        {
            "page_title": "Dashboard",
            "recent_announcements": recent_announcements,
        },
    )
