from django.urls import path

from .views import (
    SignUpWizard,
    SignInView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
    LogoutView,
    PasswordResetRequiredView,
)

urlpatterns = [
    path("sign-up/", SignUpWizard.as_view(), name="sign-up"),
    path("sign-in/", SignInView.as_view(), name="sign_in"),
    path("log-out/", LogoutView.as_view(), name="log_out"),
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
