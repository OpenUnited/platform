from django.urls import path

from .views import SignUpWizard, SignInView, ResetPasswordView

urlpatterns = [
    path("sign-up/", SignUpWizard.as_view(), name="sign-up"),
    path("sign-in/", SignInView.as_view(), name="sign-in"),
    path(
        "reset-password/",
        ResetPasswordView.as_view(),
        name="reset-password",
    ),
]
