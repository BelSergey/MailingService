from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core import cache
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView, TemplateView

from .forms import MessageForm, MailingForm
from .mixins import OwnerRequiredMixin
from .models import Message, Mailing
from .services import MailingNotAllowedError, send_mailing

def _invalidate_stats_cache():
    cache.delete(StatsView.CACHE_KEY)

class HomeView(TemplateView):
    template_name = "mailing/home.html"


class MessageListView(LoginRequiredMixin, ListView):
    model = Message
    template_name = "mailing/message_list.html"
    context_object_name = "messages_list"

    def get_queryset(self):
        user = self.request.user
        qs = Message.objects.all()
        if user.is_staff or user.is_manager:
            return qs
        return qs.filter(owner=user)


class MessageCreateView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    template_name = "mailing/message_form.html"
    success_url = reverse_lazy("mailing:message_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, "Сообщение создано.")
        return super().form_valid(form)


class MessageUpdateView(OwnerRequiredMixin, UpdateView):
    model = Message
    form_class = MessageForm
    template_name = "mailing/message_form.html"
    success_url = reverse_lazy("mailing:message_list")
    redirect_url_name = "mailing:message_list"

    def form_valid(self, form):
        messages.success(self.request, "Сообщение обновлено.")
        return super().form_valid(form)


class MessageDeleteView(OwnerRequiredMixin, DeleteView):
    model = Message
    template_name = "mailing/message_confirm_delete.html"
    success_url = reverse_lazy("mailing:message_list")
    redirect_url_name = "mailing:message_list"

    def form_valid(self, form):
        messages.success(self.request, "Сообщение удалено.")
        return super().form_valid(form)

class MailingListView(LoginRequiredMixin, ListView):
    model = Mailing
    template_name = "mailing/mailing_list.html"
    context_object_name = "mailing_list_items"

    def get_queryset(self):
        user = self.request.user
        qs = Mailing.objects.select_related("message").all()
        if user.is_staff or user.is_manager:
            return qs
        return qs.filter(owner=user)


class MailingDetailView(LoginRequiredMixin, DetailView):
    model = Mailing
    template_name = "mailing/mailing_detail.html"
    context_object_name = "mailing"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["can_manage"] = self.object.owner_id == self.request.user.id or self.request.user.is_staff
        ctx["attempts"] = self.object.attempts.select_related("recipient").all()[:50]
        return ctx


class MailingCreateView(LoginRequiredMixin, CreateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mailing/mailing_form.html"
    success_url = reverse_lazy("mailing:mailing_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, "Рассылка создана.")
        response = super().form_valid(form)
        _invalidate_stats_cache()
        return response


class MailingUpdateView(OwnerRequiredMixin, UpdateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mailing/mailing_form.html"
    success_url = reverse_lazy("mailing:mailing_list")
    redirect_url_name = "mailing:mailing_list"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Рассылка обновлена.")
        response = super().form_valid(form)
        _invalidate_stats_cache()
        return response


class MailingDeleteView(OwnerRequiredMixin, DeleteView):
    model = Mailing
    template_name = "mailing/mailing_confirm_delete.html"
    success_url = reverse_lazy("mailing:mailing_list")
    redirect_url_name = "mailing:mailing_list"

    def form_valid(self, form):
        messages.success(self.request, "Рассылка удалена.")
        response = super().form_valid(form)
        _invalidate_stats_cache()
        return response


@login_required
def send_mailing_view(request, pk):
    """Ручной запуск рассылки из интерфейса пользователя."""
    mailing = get_object_or_404(Mailing, pk=pk)
    if not (mailing.owner_id == request.user.id or request.user.is_staff or request.user.is_manager):
        messages.error(request, "У вас нет прав для отправки этой рассылки.")
        return redirect("mailing:mailing_list")

    try:
        result = send_mailing(mailing)
    except MailingNotAllowedError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(
            request,
            f"Рассылка отправлена: успешно {result['success']} из {result['total']} писем"
            + (f", ошибок: {result['failed']}." if result["failed"] else "."),
        )
    return redirect("mailing:mailing_detail", pk=mailing.pk)


@login_required
def toggle_mailing_active(request, pk):
    """Менеджер может отключить/включить рассылку (роль 'Менеджер' или staff)."""
    mailing = get_object_or_404(Mailing, pk=pk)
    user = request.user
    if not (user.is_staff or user.is_manager):
        messages.error(request, "Только менеджер может блокировать рассылки.")
        return redirect("mailing:mailing_detail", pk=mailing.pk)

    mailing.is_active = not mailing.is_active
    mailing.save(update_fields=["is_active"])
    _invalidate_stats_cache()
    state = "включена" if mailing.is_active else "отключена"
    messages.success(request, f"Рассылка {state}.")
    return redirect("mailing:mailing_detail", pk=mailing.pk)


class StatsView(LoginRequiredMixin, TemplateView):
    """
    Общая статистика по рассылкам.
    """

    template_name = "mailing/stats.html"
    CACHE_KEY = "mailing_stats_summary"
    CACHE_TTL = 60

    def get_context_data(self, **kwargs):
        from django.conf import settings
        from django.core.cache import cache

        ctx = super().get_context_data(**kwargs)

        data = cache.get(self.CACHE_KEY) if settings.CACHE_ENABLED else None
        from_cache = data is not None

        if data is None:
            data = self._collect_stats()
            if settings.CACHE_ENABLED:
                cache.set(self.CACHE_KEY, data, self.CACHE_TTL)

        ctx.update(data)
        ctx["from_cache"] = from_cache
        return ctx

    @staticmethod
    def _collect_stats():
        from clients.models import Client
        from .models import Mailing as MailingModel

        return {
            "total_mailings": MailingModel.objects.count(),
            "running_mailings": sum(
                1 for m in MailingModel.objects.all() if m.status == MailingModel.STATUS_RUNNING
            ),
            "total_clients": Client.objects.values("email").distinct().count(),
        }

