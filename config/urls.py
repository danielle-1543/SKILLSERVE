from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from accounts.views.admin.login import legacy_admin_login

urlpatterns = [
    path("admin/login/", legacy_admin_login),
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
]

# Public announcement photos only. Worker proof uses authenticated downloads.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
