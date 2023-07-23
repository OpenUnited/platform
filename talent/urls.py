from django.urls import path
from . import views


urlpatterns = [
    path("signin", views.sign_in, name="sign_in"),
    path("signup", views.sign_up, name="sign_up"),
    path("logout", views.log_out, name="log_out"),
    path("reset_password", views.reset_password, name="reset_password"),
    path("complete_profile", views.complete_profile, name="complete_profile"),
]
