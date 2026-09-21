from django.contrib.auth.models import AbstractUser
from django.db import models
import PIL


class User(AbstractUser):

    ROLE_USER = "user"
    ROLE_MANAGER = "manager"
    ROLE_CHOICES = [
        (ROLE_USER, "Пользователь"),
        (ROLE_MANAGER, "Менеджер"),
    ]

    email = models.EmailField(unique=True, verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    country = models.CharField(max_length=50, blank=True, verbose_name="Страна")
    avatar = models.ImageField(upload_to="users/avatars/", blank=True, null=True, verbose_name="Аватар")
    is_email_confirmed = models.BooleanField(default=False, verbose_name="Email подтверждён")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_USER, verbose_name="Роль")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.email

    @property
    def is_manager(self):
        return self.role == self.ROLE_MANAGER or self.groups.filter(name="Менеджеры").exists()