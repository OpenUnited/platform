from django.urls import path
from . import views


urlpatterns = [
    path("signin", views.sign_in, name="sign_in"),
    path("signup", views.sign_up, name="sign_up"),
    path("logout", views.log_out, name="log_out"),
]
