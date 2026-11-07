"""Each route imports its corresponding feature file."""
from django.contrib.auth.views import LogoutView
from django.urls import path
from accounts.views.public import peso_home, skillserve_home, announcement
from accounts.views.auth import login, signup
from accounts.views.admin import dashboard as admin_dashboard, login as admin_login, announcements, worker_verification
from accounts.views.worker import dashboard as worker_dashboard, profile as worker_profile, proof_preview
from accounts.views.client import dashboard as client_dashboard
from accounts.views.worker import posts as worker_posts
from accounts.views.client import search, worker_profile as client_profiles, bookmarks, reports
from accounts.views.client import profile as client_profile
from accounts.views.admin import skills_catalog
from accounts.views import messaging
from accounts.views import job_offers
from accounts.views import bookings, chat_attachments
from accounts.views.admin import reports as admin_reports

urlpatterns = [
    path('admin-dashboard/skills/', skills_catalog.skills_catalog, name='skills_catalog'),
    path('jobs/files/<int:pk>/', job_offers.job_attachment, name='job_attachment'),
    path('jobs/', job_offers.job_offers, name='job_offers'),
    path('jobs/new/', job_offers.create_job_offer, name='create_job_offer'),
    path('jobs/<int:pk>/', job_offers.job_offer_detail, name='job_offer_detail'),
    path('jobs/<int:pk>/close/', job_offers.close_job_offer, name='close_job_offer'),
    path('jobs/<int:pk>/message/', job_offers.message_job_client, name='message_job_client'),
    # Public pages.
    path("", peso_home.landing, name="landing"),
    path("announcements/<int:pk>/", announcement.public_announcement, name="public_announcement"),
    path("skillserve/", skillserve_home.skillserve_landing, name="skillserve_landing"),

    # Shared authentication.
    path("login/", login.MemberLoginView.as_view(), name="login"),
    path("signup/", signup.signup, name="signup"),
    path("logout/", LogoutView.as_view(next_page="landing"), name="logout"),

    # Client dashboard and existing role-aware entry URL.
    path("dashboard/", client_dashboard.client_dashboard, name="skillserve_dashboard"),
    path("client/profile/", client_profile.my_profile, name="client_profile"),
    path("clients/<int:pk>/", client_profile.public_profile, name="public_client_profile"),
    path("workers/search/", search.search_workers, name="search_workers"),
    path("workers/<int:pk>/", client_profiles.worker_profile, name="client_worker_profile"),
    path("workers/<int:pk>/bookmark/", bookmarks.toggle_bookmark, name="bookmark_worker"),
    path("workers/<int:pk>/report/", reports.report_worker, name="report_worker"),
    path("workers/<int:pk>/message/", messaging.start_conversation, name="start_conversation"),
    path("saved-workers/", bookmarks.saved_workers, name="saved_workers"),
    path("messages/", messaging.inbox, name="inbox"),
    path("messages/<int:pk>/", messaging.conversation, name="conversation"),
    path("messages/<int:pk>/updates/", messaging.chat_updates, name="chat_updates"),
    path("messages/attachments/<int:pk>/", chat_attachments.chat_attachment, name="chat_attachment"),
    path("messages/<int:pk>/book/", bookings.request_booking, name="request_booking"),
    path("bookings/<int:pk>/status/", bookings.update_booking, name="update_booking"),
    path("messages/<int:pk>/message/<int:message_id>/", messaging.message_action, name="message_action"),
    path("admin-dashboard/reports/", admin_reports.reported_workers, name="reported_workers"),

    # Worker dashboard (existing profile URL preserved), profile editing, and private proof.
    path("worker/profile/", worker_dashboard.worker_dashboard, name="worker_profile"),
    path("worker/posts/", worker_posts.manage_worker_post, name="worker_posts"),
    path("worker/profile/edit/", worker_profile.edit_worker_profile, name="edit_worker_profile"),
    path("worker/proof/<int:pk>/", proof_preview.worker_evidence, name="worker_evidence"),
    
    # Administrator features.
    path("admin-login/", admin_login.legacy_admin_login, name="admin_login"),
    path("admin-dashboard/", admin_dashboard.admin_dashboard, name="admin_dashboard"),
    path("admin-dashboard/announcements/", announcements.CRUD_annoucements, name="CRUD_annoucements"),
    path("admin-dashboard/workers/", worker_verification.worker_reviews, name="worker_reviews"),
    path("admin-dashboard/workers/<int:pk>/", worker_verification.review_worker, name="review_worker"),
]
