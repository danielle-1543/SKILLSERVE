from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


# Make SkillServe accounts manageable through Django's admin site.
# UserAdmin supplies Django's existing account management forms.
@admin.register(User)
class SkillServeUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("SkillServe account", {"fields": ("role",)}),)
    list_display = UserAdmin.list_display + ("role",)
