from django.urls import path
from .views import (
    ChallengeAuthoringView,
    SkillsListView,
    ExpertiseListView,
)

app_name = 'challenge_authoring'

urlpatterns = [
    path(
        "product/<str:product_slug>/flows/challenge-authoring/create/",
        ChallengeAuthoringView.as_view(),
        name="create"
    ),
    path(
        "skills/",
        SkillsListView.as_view(),
        name="skills"
    ),
    path(
        "skills/<int:skill_id>/expertise/",
        ExpertiseListView.as_view(),
        name="expertise"
    ),
]

