from django.contrib import admin
from .models import Mailing, MailingAttempt, Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "owner", "created_at")
    search_fields = ("subject",)


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ("id", "message", "owner", "start_time", "end_time", "status", "is_active")
    list_filter = ("is_active",)

    @admin.display(description="Статус")
    def status(self, obj):
        return obj.get_status_display()


@admin.register(MailingAttempt)
class MailingAttemptAdmin(admin.ModelAdmin):
    list_display = ("mailing", "recipient", "status", "attempted_at")
    list_filter = ("status",)