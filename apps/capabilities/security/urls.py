from django.urls import path
from django.shortcuts import redirect
from django.contrib.auth.views import LogoutView

from .views import (
    LogoutView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetRequiredView,
    PasswordResetView,
    SignInView,
    SignUpWizard,
)

app_name = 'security'

urlpatterns = [
    path("sign-up/", SignUpWizard.as_view(), name="sign_up"),
    path("sign-in/", SignInView.as_view(), name="sign_in"),
    path("logout/", LogoutView.as_view(next_page='/'), name="logout"),
    path(
        "password-reset-required/",
        PasswordResetRequiredView.as_view(),
        name="password_reset_required",
    ),
]

urlpatterns += [
    path(
        "password-reset/",
        PasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "password-reset-confirm/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "password-reset-complete/",
        PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
]
