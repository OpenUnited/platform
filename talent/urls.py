from django.urls import path
from .views import SignUpWizard, SignInView
from . import views

urlpatterns = [
    path("sign-up/", SignUpWizard.as_view(), name="sign-up"),
    path("sign-in/", SignInView.as_view(), name="sign-in"),
    path("reset-password/", views.reset_password, name="reset-password"),
    path("logout/", views.log_out, name="log_out"),
]
