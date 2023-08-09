from django.urls import path

from . import views

urlpatterns = [
    path("logout/", views.log_out, name="log_out"),
]
