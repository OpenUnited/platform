from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth import logout
from django.utils.translation import gettext_lazy as _


from django.contrib.auth.views import (
    LogoutView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.urls import reverse_lazy

from .forms import ResetPasswordForm
from .models import Person


class ResetPasswordView(PasswordResetView):
    form_class = ResetPasswordForm
    template_name = "talent/reset_password.html"
    success_url = reverse_lazy("home")

    def get(self, request, *args, **kwargs):
        form = self.form_class(initial=self.initial)
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            email = form.cleaned_data["email"]
            if Person.objects.filter(email=email).exists():
                return self.form_valid(form)
        else:
            form.add_error(None, _("TODO: add an error message"))

        return render(request, self.template_name, {"form": form})


def reset_password(request):
    return HttpResponse("reset password")


def log_out(request):
    logout(request)
    return redirect("home")
