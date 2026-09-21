from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("email", "username", "role", "is_email_confirmed", "is_active", "is_staff")
    list_filter = ("role", "is_email_confirmed", "is_active")
    fieldsets = UserAdmin.fieldsets + (
        ("Дополнительно", {"fields": ("phone", "country", "avatar", "is_email_confirmed", "role")}),
    )