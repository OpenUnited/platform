from django.urls import path
from .views import (
    ChallengeAuthoringView,
    SkillsListView,
    ExpertiseListView,
    bounty_table,
    remove_bounty,
)

app_name = 'challenge_authoring'

urlpatterns = [
    path(
        "product/<str:product_slug>/flows/challenge-authoring/create/",
        ChallengeAuthoringView.as_view(),
        name="create"
    ),
    path(
        "product/<str:product_slug>/flows/challenge-authoring/bounty-table/",
        bounty_table,
        name="bounty_table"
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
    path('bounty/<int:bounty_id>/remove/', remove_bounty, name='remove_bounty'),
]

