from django.conf import settings
from django.db import models


class Message(models.Model):
    """Сообщение для рассылки."""

    subject = models.CharField(max_length=255, verbose_name="Тема письма")
    body = models.TextField(verbose_name="Тело письма")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="Владелец",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ["-created_at"]

    def __str__(self):
        return self.subject
class Mailing(models.Model):
    """Рассылка сообщения группе получателей."""

    STATUS_CREATED = "created"
    STATUS_RUNNING = "running"
    STATUS_FINISHED = "finished"
    STATUS_CHOICES = [
        (STATUS_CREATED, "Создана"),
        (STATUS_RUNNING, "Запущена"),
        (STATUS_FINISHED, "Завершена"),
    ]

    start_time = models.DateTimeField(verbose_name="Дата и время начала отправки")
    end_time = models.DateTimeField(verbose_name="Дата и время окончания отправки")
    message = models.ForeignKey(
        Message, on_delete=models.CASCADE, related_name="mailings", verbose_name="Сообщение"
    )
    recipients = models.ManyToManyField(
        "clients.Client", related_name="mailings", verbose_name="Получатели"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mailings",
        verbose_name="Владелец",
    )
    is_active = models.BooleanField(
        default=True, verbose_name="Активна", help_text="Менеджер может отключить рассылку"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Рассылка «{self.message.subject}» ({self.get_status_display()})"

    def clean(self):
        from django.core.exceptions import ValidationError
        from django.utils import timezone

        errors = {}
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            errors["end_time"] = "Дата окончания должна быть позже даты начала."
        if self.start_time and self._state.adding and self.start_time < timezone.now():
            errors["start_time"] = "Дата начала не может быть в прошлом."
        if errors:
            raise ValidationError(errors)

    @property
    def status(self):
        """Статус вычисляется динамически при каждом обращении."""
        from django.utils import timezone

        now = timezone.now()
        if not self.is_active:
            return self.STATUS_FINISHED
        if now < self.start_time:
            return self.STATUS_CREATED
        if self.start_time <= now <= self.end_time:
            return self.STATUS_RUNNING
        return self.STATUS_FINISHED

    def get_status_display(self):
        return dict(self.STATUS_CHOICES)[self.status]

    def is_sendable_now(self):
        """Проверка, разрешена ли отправка в данный момент по условиям задания."""
        from django.utils import timezone

        now = timezone.now()
        return self.is_active and self.start_time <= now <= self.end_time


class MailingAttempt(models.Model):
    """Попытка отправки письма в рамках рассылки одному получателю."""

    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_SUCCESS, "Успешно"),
        (STATUS_FAILED, "Не успешно"),
    ]

    mailing = models.ForeignKey(
        Mailing, on_delete=models.CASCADE, related_name="attempts", verbose_name="Рассылка"
    )
    recipient = models.ForeignKey(
        "clients.Client", on_delete=models.CASCADE, related_name="attempts", verbose_name="Получатель"
    )
    attempted_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время попытки")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, verbose_name="Статус")
    server_response = models.TextField(blank=True, verbose_name="Ответ почтового сервера")

    class Meta:
        verbose_name = "Попытка рассылки"
        verbose_name_plural = "Попытки рассылки"
        ordering = ["-attempted_at"]

    def __str__(self):
        return f"{self.mailing_id} -> {self.recipient.email}: {self.status}"
