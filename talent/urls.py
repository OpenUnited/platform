from django.urls import path

from . import views
from .views import ProfileView

urlpatterns = [
    path("profile/<int:pk>/", ProfileView.as_view(), name="profile"),
    path(
        "profile/<int:pk>/remove-picture/", views.remove_picture, name="remove_picture"
    ),
]
