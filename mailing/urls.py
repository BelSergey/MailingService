from django.urls import path
from . import views

app_name = "mailing"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("messages/", views.MessageListView.as_view(), name="message_list"),
    path("messages/add/", views.MessageCreateView.as_view(), name="message_create"),
    path("messages/<int:pk>/edit/", views.MessageUpdateView.as_view(), name="message_update"),
    path("messages/<int:pk>/delete/", views.MessageDeleteView.as_view(), name="message_delete"),
    path("mailings/", views.MailingListView.as_view(), name="mailing_list"),
    path("mailings/add/", views.MailingCreateView.as_view(), name="mailing_create"),
    path("mailings/<int:pk>/", views.MailingDetailView.as_view(), name="mailing_detail"),
    path("mailings/<int:pk>/edit/", views.MailingUpdateView.as_view(), name="mailing_update"),
    path("mailings/<int:pk>/delete/", views.MailingDeleteView.as_view(), name="mailing_delete"),
    path("mailings/<int:pk>/send/", views.send_mailing_view, name="mailing_send"),
    path("mailings/<int:pk>/toggle-active/", views.toggle_mailing_active, name="mailing_toggle_active"),
    path("stats/", views.StatsView.as_view(), name="stats"),
]