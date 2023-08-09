from django.urls import path
from django.contrib.auth.views import (
    LogoutView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)

from .views import ResetPasswordView
from . import views

urlpatterns = [
    path(
        "reset-password/",
        ResetPasswordView.as_view(),
        name="reset-password",
    ),
    path("logout/", views.log_out, name="log_out"),
]
