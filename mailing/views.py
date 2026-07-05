from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView, TemplateView

from .forms import MessageForm
from .mixins import OwnerRequiredMixin
from .models import Message


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
