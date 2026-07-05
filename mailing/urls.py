from django.urls import path
from . import views

app_name = "mailing"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("messages/", views.MessageListView.as_view(), name="message_list"),
    path("messages/add/", views.MessageCreateView.as_view(), name="message_create"),
    path("messages/<int:pk>/edit/", views.MessageUpdateView.as_view(), name="message_update"),
    path("messages/<int:pk>/delete/", views.MessageDeleteView.as_view(), name="message_delete"),
]