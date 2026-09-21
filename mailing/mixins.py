from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class OwnerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Изменять/удалять объект может только его владелец (или staff)."""

    redirect_url_name = None

    def test_func(self):
        obj = self.get_object()
        user = self.request.user
        return obj.owner_id == user.id or user.is_staff

    def handle_no_permission(self):
        messages.error(self.request, "У вас нет прав для выполнения этого действия.")
        from django.shortcuts import redirect
        return redirect(self.redirect_url_name or "mailing:home")