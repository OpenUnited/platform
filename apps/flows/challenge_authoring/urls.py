from django.urls import path
from .views import (
    ChallengeAuthoringView,
    SkillsListView,
    ExpertiseListView,
    BountyModalView
)

app_name = 'challenge_authoring'

urlpatterns = [
    path(
        "product/<str:product_slug>/flows/challenge-authoring/create/",
        ChallengeAuthoringView.as_view(),
        name="create"
    ),
    path(
        "product/<str:product_slug>/flows/challenge-authoring/skills/",
        SkillsListView.as_view(),
        name="skills"
    ),
    path(
        "product/<str:product_slug>/flows/challenge-authoring/skills/<int:skill_id>/expertise/",
        ExpertiseListView.as_view(),
        name="skill_expertise"
    ),
    path(
        "product/<str:product_slug>/flows/challenge-authoring/bounty-modal/",
        BountyModalView.as_view(),
        name="bounty_modal"
    ),
]

