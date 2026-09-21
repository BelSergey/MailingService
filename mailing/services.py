from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import Mailing, MailingAttempt


class MailingNotAllowedError(Exception):
    """Выбрасывается, если отправка рассылки сейчас не разрешена."""


def send_mailing(mailing: Mailing) -> dict:
    """
    Отправляет письмо каждому получателю рассылки.
    Возвращает словарь со статистикой отправки.
    """
    if not mailing.is_sendable_now():
        raise MailingNotAllowedError(
            "Отправка невозможна: текущее время вне разрешённого интервала рассылки "
            "либо рассылка деактивирована."
        )

    recipients = list(mailing.recipients.all())
    attempts_to_create = []
    success_count = 0
    failed_count = 0

    for recipient in recipients:
        try:
            send_mail(
                subject=mailing.message.subject,
                message=mailing.message.body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                fail_silently=False,
            )
        except Exception as exc:
            attempts_to_create.append(
                MailingAttempt(
                    mailing=mailing,
                    recipient=recipient,
                    status=MailingAttempt.STATUS_FAILED,
                    server_response=str(exc),
                )
            )
            failed_count += 1
        else:
            attempts_to_create.append(
                MailingAttempt(
                    mailing=mailing,
                    recipient=recipient,
                    status=MailingAttempt.STATUS_SUCCESS,
                    server_response="OK",
                )
            )
            success_count += 1

    MailingAttempt.objects.bulk_create(attempts_to_create)

    return {
        "total": len(recipients),
        "success": success_count,
        "failed": failed_count,
        "sent_at": timezone.now(),
    }
