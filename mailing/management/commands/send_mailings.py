from django.core.management.base import BaseCommand, CommandError

from mailing.models import Mailing
from mailing.services import MailingNotAllowedError, send_mailing


class Command(BaseCommand):
    help = (
        "Отправляет рассылки по требованию из командной строки. "
        "Без аргументов отправляет все рассылки в статусе 'Запущена'."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "mailing_id",
            nargs="?",
            type=int,
            help="ID конкретной рассылки для отправки (необязательно).",
        )

    def handle(self, *args, **options):
        mailing_id = options.get("mailing_id")

        if mailing_id:
            try:
                mailings = [Mailing.objects.get(pk=mailing_id)]
            except Mailing.DoesNotExist as exc:
                raise CommandError(f"Рассылка с id={mailing_id} не найдена.") from exc
        else:
            mailings = [m for m in Mailing.objects.all() if m.status == Mailing.STATUS_RUNNING]

        if not mailings:
            self.stdout.write(self.style.WARNING("Нет рассылок, доступных для отправки."))
            return

        for mailing in mailings:
            try:
                result = send_mailing(mailing)
            except MailingNotAllowedError as exc:
                self.stdout.write(self.style.ERROR(f"Рассылка #{mailing.pk}: {exc}"))
                continue
            self.stdout.write(
                self.style.SUCCESS(
                    f"Рассылка #{mailing.pk}: отправлено {result['success']} из {result['total']}"
                    f" (ошибок: {result['failed']})."
                )
            )
