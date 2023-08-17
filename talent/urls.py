from django.urls import path

from .views import ProfileView, get_skills, get_expertise

urlpatterns = [
    path("profile/<int:pk>/", ProfileView.as_view(), name="profile"),
    path("get-skills/", get_skills, name="get_skills"),
    path("get-expertise/", get_expertise, name="get_expertise"),
]
