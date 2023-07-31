from django.urls import path

from .views import (
    ChallengeListView,
    ProductListView,
    challenge_detail,
    product_detail,
    product_redirect,
    product_summary,
    product_initiatives,
    product_challenges,
    product_ideas_bugs,
    product_tree,
    product_people,
)

urlpatterns = [
    path("challenges/", ChallengeListView.as_view(), name="challenges"),
    path("products/", ProductListView.as_view(), name="products"),
    path(
        "<str:organisation_username>/<str:product_slug>/challenge/<int:challenge_id>",
        challenge_detail,
        name="challenge_detail",
    ),
    path(
        "<str:organisation_username>/<str:product_slug>/",
        product_redirect,
    ),
    path(
        "<str:organisation_username>/<str:product_slug>/summary",
        product_summary,
        name="product_summary",
    ),
    path(
        "<str:organisation_username>/<str:product_slug>/initiatives",
        product_initiatives,
        name="product_initiatives",
    ),
    path(
        "<str:organisation_username>/<str:product_slug>/challenge",
        product_challenges,
        name="product_challenges",
    ),
    path(
        "<str:organisation_username>/<str:product_slug>/tree",
        product_tree,
        name="product_tree",
    ),
    path(
        "<str:organisation_username>/<str:product_slug>/ideas",
        product_ideas_bugs,
        name="product_ideas_bugs",
    ),
    path(
        "<str:organisation_username>/<str:product_slug>/people",
        product_people,
        name="product_people",
    ),
]
