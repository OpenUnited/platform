from django.urls import path

from .views import (
    BountyDeliveryAttemptDetail,
    CreateBountyDeliveryAttemptView,
    CreateFeedbackView,
    DeleteFeedbackView,
    GetExpertiseView,
    TalentShowcase,
    UpdateFeedbackView,
    UpdateProfileView,
    get_current_expertise,
    get_current_skills,
    get_skills,
    list_skill_and_expertise,
    status_and_points,
)

urlpatterns = [
    path("showcase/<str:username>/", TalentShowcase.as_view(), name="showcase"),
    path("profile/<int:pk>/", UpdateProfileView.as_view(), name="profile"),
    path("get-skills/", get_skills, name="get_skills"),
    path("get-current-skills/", get_current_skills, name="get_current_skills"),
    path("get-expertise/", GetExpertiseView.as_view(), name="get_expertise"),
    path(
        "get-current-expertise/",
        get_current_expertise,
        name="get_current_expertise",
    ),
    path(
        "list-skill-and-expertise/",
        list_skill_and_expertise,
        name="list-skill-and-expertise",
    ),
    path("status-and-points", status_and_points, name="status-and-points"),
    path(
        "feedback/create/",
        CreateFeedbackView.as_view(),
        name="create-feedback",
    ),
    path(
        "feedback/update/<int:pk>/",
        UpdateFeedbackView.as_view(),
        name="update-feedback",
    ),
    path(
        "feedback/delete/<int:pk>",
        DeleteFeedbackView.as_view(),
        name="delete-feedback",
    ),
    path(
        "<str:product_slug>/challenges/<int:challenge_id>/bounties/<int:bounty_id>/submissions/create",
        CreateBountyDeliveryAttemptView.as_view(),
        name="create-bounty-delivery-attempt",
    ),
    path(
        "<str:product_slug>/challenges/<int:challenge_id>/bounties/<int:bounty_id>/submissions/<int:pk>/",
        BountyDeliveryAttemptDetail.as_view(),
        name="bounty-delivery-attempt-detail",
    ),
]
