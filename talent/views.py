from django.shortcuts import redirect, HttpResponse
from django.contrib.auth import logout
from django.utils.translation import gettext_lazy as _


def reset_password(request):
    return HttpResponse("reset password")


def log_out(request):
    logout(request)
    return redirect("home")
