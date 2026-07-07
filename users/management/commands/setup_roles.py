from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from clients.models import Client
from mailing.models import Mailing, MailingAttempt, Message


class Command(BaseCommand):
    help = (
        "Создаёт группу 'Менеджеры' с правами на просмотр всех рассылок/клиентов/сообщений "
        "и на отключение рассылок, а также правом блокировки пользователей."
    )

    def handle(self, *args, **options):
        group, created = Group.objects.get_or_create(name="Менеджеры")

        view_perms = []
        for model in (Client, Message, Mailing, MailingAttempt):
            ct = ContentType.objects.get_for_model(model)
            view_perms.append(Permission.objects.get(content_type=ct, codename=f"view_{model._meta.model_name}"))

        # право отключать рассылки соответствует стандартному change_mailing
        ct_mailing = ContentType.objects.get_for_model(Mailing)
        change_mailing = Permission.objects.get(content_type=ct_mailing, codename="change_mailing")

        from django.contrib.auth import get_user_model
        User = get_user_model()
        ct_user = ContentType.objects.get_for_model(User)
        change_user = Permission.objects.get(content_type=ct_user, codename="change_user")

        group.permissions.set(view_perms + [change_mailing, change_user])

        status = "создана" if created else "уже существовала"
        self.stdout.write(self.style.SUCCESS(f"Группа 'Менеджеры' {status}. Права назначены."))
