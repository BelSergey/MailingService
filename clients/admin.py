from django.contrib import admin
from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "owner", "created_at")
    search_fields = ("full_name", "email")
    list_filter = ("owner",)