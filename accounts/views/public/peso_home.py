"""Public PESO homepage and category filtering."""
from django.shortcuts import render
from core.models import Announcement


def landing(request):
    category = request.GET.get("category", Announcement.Category.GENERAL)
    posts = Announcement.objects.select_related("author").order_by("-created_at", "-pk")
    if category != "all":
        if category not in dict(Announcement.Category.choices):
            category = Announcement.Category.GENERAL
        posts = posts.filter(category=category)
    return render(request, "public/dashboard.html", {
        "announcements": posts,
        "pinned_posts": Announcement.objects.select_related("author").filter(is_pinned=True)[:4],
        "categories": Announcement.Category.choices,
        "selected_category": category,
    })
