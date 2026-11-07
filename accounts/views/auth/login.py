"""Member login and post-login routing by account role."""
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from accounts.models import WorkerProfile
from core.models import Announcement


class MemberLoginView(LoginView):
    template_name = "public/skillserve.html"
    next_page = reverse_lazy("skillserve_dashboard")

    def get_success_url(self):
        if self.request.user.is_administrator:
            return str(reverse_lazy("admin_dashboard"))
        if self.request.user.role == "worker":
            profile = WorkerProfile.objects.filter(user=self.request.user).first()
            return str(reverse_lazy("edit_worker_profile" if not profile or profile.status == "draft" else "worker_profile"))
        if self.request.user.role == 'client':
            return str(reverse_lazy('skillserve_dashboard'))
        return super().get_success_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "announcements": Announcement.objects.select_related("author").order_by("-created_at", "-pk"),
            "pinned_posts": Announcement.objects.filter(is_pinned=True)[:4],
            "categories": Announcement.Category.choices,
            "open_login": True,
        })
        return context
