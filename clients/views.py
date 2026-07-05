from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import ClientForm
from .models import Client


class OwnerOrManagerMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Разрешает доступ владельцу объекта либо пользователю с ролью менеджера/staff."""

    def test_func(self):
        obj = self.get_object()
        user = self.request.user
        return obj.owner_id == user.id or user.is_staff or user.is_manager

    def handle_no_permission(self):
        messages.error(self.request, "У вас нет прав для выполнения этого действия.")
        return redirect("clients:client_list")


class ClientListView(LoginRequiredMixin, ListView):
    model = Client
    template_name = "clients/client_list.html"
    context_object_name = "clients"

    def get_queryset(self):
        user = self.request.user
        qs = Client.objects.all()
        if user.is_staff or user.is_manager:
            return qs
        return qs.filter(owner=user)


class ClientCreateView(LoginRequiredMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = "clients/client_form.html"
    success_url = reverse_lazy("clients:client_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, "Получатель добавлен.")
        return super().form_valid(form)


class ClientUpdateView(OwnerOrManagerMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = "clients/client_form.html"
    success_url = reverse_lazy("clients:client_list")

    def test_func(self):
        obj = self.get_object()
        return obj.owner_id == self.request.user.id or self.request.user.is_staff

    def form_valid(self, form):
        messages.success(self.request, "Получатель обновлён.")
        return super().form_valid(form)


class ClientDeleteView(OwnerOrManagerMixin, DeleteView):
    model = Client
    template_name = "clients/client_confirm_delete.html"
    success_url = reverse_lazy("clients:client_list")

    def test_func(self):
        obj = self.get_object()
        return obj.owner_id == self.request.user.id or self.request.user.is_staff

    def form_valid(self, form):
        messages.success(self.request, "Получатель удалён.")
        return super().form_valid(form)
