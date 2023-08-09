from django.shortcuts import redirect
from django.contrib.auth import logout
from django.utils.translation import gettext_lazy as _


def log_out(request):
    logout(request)
    return redirect("home")
