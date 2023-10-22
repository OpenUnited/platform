from django.urls import path

from .views import start_backup


urlpatterns = [
    path("start/", start_backup, name="start_backup"),
]
