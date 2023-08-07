from django.urls import path
from .views import SignUpWizard
from . import views

urlpatterns = [
    path("sign-up/", SignUpWizard.as_view(), name="sign-up"),
    path("sign-in/", views.sign_in, name="sign-in"),
    path("logout/", views.log_out, name="log_out"),
]
