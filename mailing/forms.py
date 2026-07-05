from django import forms
from django.utils import timezone
from .models import Message, Mailing


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["subject", "body"]
        widgets = {"body": forms.Textarea(attrs={"rows": 8})}

class MailingForm(forms.ModelForm):
    class Meta:
        model = Mailing
        fields = ["start_time", "end_time", "message", "recipients"]
        widgets = {
            "start_time": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "end_time": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "recipients": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["start_time"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["end_time"].input_formats = ["%Y-%m-%dT%H:%M"]
        if user is not None and not (user.is_staff or user.is_manager):
            self.fields["message"].queryset = self.fields["message"].queryset.model.objects.filter(owner=user)
            self.fields["recipients"].queryset = self.fields["recipients"].queryset.model.objects.filter(owner=user)

    def clean(self):
        cleaned = super().clean()
        start_time = cleaned.get("start_time")
        end_time = cleaned.get("end_time")
        if start_time and end_time and start_time >= end_time:
            self.add_error("end_time", "Дата окончания должна быть позже даты начала.")
        if start_time and not self.instance.pk and start_time < timezone.now():
            self.add_error("start_time", "Дата начала не может быть в прошлом.")
        return cleaned

