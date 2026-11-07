"""Public individual announcement opened from a shared link."""
from django.shortcuts import get_object_or_404, render
from core.models import Announcement


def public_announcement(request, pk):
    post = get_object_or_404(Announcement.objects.select_related("author"), pk=pk)
    return render(request, "public/announcement.html", {"post": post})
