from django.urls import path

from .views import ChallengeListView, ProductListView, challenge_detail

urlpatterns = [
    path("challenges/", ChallengeListView.as_view(), name="challenges"),
    path("products/", ProductListView.as_view(), name="products"),
    path(
        "<str:organisation_username>/<str:product_slug>/challenge/<int:challenge_id>",
        challenge_detail,
        name="challenge_detail",
    ),
]
