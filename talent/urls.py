from django.urls import path

from .views import (
    UpdateProfileView,
    get_skills,
    get_expertise,
    list_skill_and_expertise,
    TalentPortfolio,
    status_and_points,
    submit_feedback,
)

urlpatterns = [
    path("portfolio/<str:username>", TalentPortfolio.as_view(), name="portfolio"),
    path("profile/<int:pk>/", UpdateProfileView.as_view(), name="profile"),
    path("get-skills/", get_skills, name="get_skills"),
    path("get-expertise/", get_expertise, name="get_expertise"),
    path(
        "list-skill-and-expertise/",
        list_skill_and_expertise,
        name="list-skill-and-expertise",
    ),
    path("status-and-points", status_and_points, name="status-and-points"),
    path("submit-feedback/", submit_feedback, name="submit-feedback"),
]
