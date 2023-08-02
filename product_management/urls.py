from django.urls import path

from .views import (
    ChallengeListView,
    ProductListView,
    challenge_detail,
    product_redirect,
    ProductSummaryView,
    ProductInitiativesView,
    ProductTreeView,
    ProductIdeasAndBugsView,
    ProductChallengesView,
    ProductPeopleView,
    initiative_details,
    capability_detail,
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
        ProductSummaryView.as_view(),
        name="product_summary",
    ),
    path(
        "<str:organisation_username>/<str:product_slug>/initiatives",
        ProductInitiativesView.as_view(),
        name="product_initiatives",
    ),
    path(
        "<str:organisation_username>/<str:product_slug>/challenges",
        ProductChallengesView.as_view(),
        name="product_challenges",
    ),
    path(
        "<str:organisation_username>/<str:product_slug>/challenge/<int:challenge_id>",
        challenge_detail,
        name="challenge_detail",
    ),
    path(
        "<str:organisation_username>/<str:product_slug>/tree",
        ProductTreeView.as_view(),
        name="product_tree",
    ),
    path(
        "<str:organisation_username>/<str:product_slug>/ideas",
        ProductIdeasAndBugsView.as_view(),
        name="product_ideas_bugs",
    ),
    path(
        "<str:organisation_username>/<str:product_slug>/people",
        ProductPeopleView.as_view(),
        name="product_people",
    ),
    path(
        "<str:organisation_username>/<str:product_slug>/initiative/<int:initiative_id>",
        initiative_details,
        name="initiative_details",
    ),
    path(
        "<str:organisation_username>/<str:product_slug>/capability/<int:capability_id>",
        capability_detail,
        name="capability_detail",
    ),
]
