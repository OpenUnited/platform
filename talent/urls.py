from django.urls import path

from .views import (
    UpdateProfileView,
    get_skills,
    get_current_skills,
    get_expertise,
    get_current_expertise,
    list_skill_and_expertise,
    TalentPortfolio,
    status_and_points,
    CreateFeedbackView,
    UpdateFeedbackView,
    DeleteFeedbackView,
)

urlpatterns = [
    path("portfolio/<str:username>", TalentPortfolio.as_view(), name="portfolio"),
    path("profile/<int:pk>/", UpdateProfileView.as_view(), name="profile"),
    path("get-skills/", get_skills, name="get_skills"),
    path("get-current-skills/", get_current_skills, name="get_current_skills"),
    path("get-expertise/", get_expertise, name="get_expertise"),
    path("get-current-expertise/", get_current_expertise, name="get_current_expertise"),
    path(
        "list-skill-and-expertise/",
        list_skill_and_expertise,
        name="list-skill-and-expertise",
    ),
    path("status-and-points", status_and_points, name="status-and-points"),
    path("feedback/create/", CreateFeedbackView.as_view(), name="create-feedback"),
    path(
        "feedback/update/<int:pk>/",
        UpdateFeedbackView.as_view(),
        name="update-feedback",
    ),
    path(
        "feedback/delete/<int:pk>", DeleteFeedbackView.as_view(), name="delete-feedback"
    ),
]
