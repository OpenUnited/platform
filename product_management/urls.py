from django.urls import path

from .views import (
    ChallengeListView,
    ProductListView,
    ProductRedirectView,
    ProductSummaryView,
    ProductInitiativesView,
    ProductTreeView,
    ProductIdeasAndBugsView,
    CreateProductIdea,
    UpdateProductIdea,
    ProductIdeaDetail,
    ProductChallengesView,
    ProductRoleAssignmentView,
    ChallengeDetailView,
    InitiativeDetailView,
    CapabilityDetailView,
    BountyClaimView,
    CreateProductView,
    CreateOrganisationView,
    CreateChallengeView,
    UpdateChallengeView,
    DeleteChallengeView,
    UpdateProductView,
)

# Developer's Note: I separated the urlpatterns because I found it convenient to do like this.
# It looked too ugly when putting every path into a single list.
#
# If a new path requires to be added, add it to their corresponding part. If it does not fit
# any of the existing groups, you can add an additional group.


# URL patterns for challenge and product list views
urlpatterns = [
    path("challenges/", ChallengeListView.as_view(), name="challenges"),
    path("challenge/create/", CreateChallengeView.as_view(), name="create-challenge"),
    path(
        "challenge/update/<int:pk>/",
        UpdateChallengeView.as_view(),
        name="update-challenge",
    ),
    path(
        "challenge/delete/<int:pk>/",
        DeleteChallengeView.as_view(),
        name="delete-challenge",
    ),
    path("products/", ProductListView.as_view(), name="products"),
    path("bounty-claim/", BountyClaimView.as_view(), name="bounty-claim"),
    path("product/create", CreateProductView.as_view(), name="create-product"),
    path(
        "product/update/<int:pk>/", UpdateProductView.as_view(), name="update-product"
    ),
    path(
        "organisation/create",
        CreateOrganisationView.as_view(),
        name="create-organisation",
    ),
]

# URL patterns for various product views
urlpatterns += [
    path(
        "<str:product_slug>/",
        ProductRedirectView.as_view(),
        name="product_detail",
    ),
    path(
        "<str:product_slug>/summary",
        ProductSummaryView.as_view(),
        name="product_summary",
    ),
    path(
        "<str:product_slug>/initiatives",
        ProductInitiativesView.as_view(),
        name="product_initiatives",
    ),
    path(
        "<str:product_slug>/challenges",
        ProductChallengesView.as_view(),
        name="product_challenges",
    ),
    path(
        "<str:product_slug>/tree",
        ProductTreeView.as_view(),
        name="product_tree",
    ),
    path(
        "<str:product_slug>/ideas",
        ProductIdeasAndBugsView.as_view(),
        name="product_ideas_bugs",
    ),
    path(
        "<str:product_slug>/ideas/new",
        CreateProductIdea.as_view(),
        name="add_product_idea",
    ),
    path(
        "<str:product_slug>/idea/<int:pk>",
        ProductIdeaDetail.as_view(),
        name="product_idea_detail",
    ),
    path(
        "<str:product_slug>/ideas/update/<int:pk>",
        UpdateProductIdea.as_view(),
        name="update_product_idea",
    ),
    path(
        "<str:product_slug>/people",
        ProductRoleAssignmentView.as_view(),
        name="product_people",
    ),
]

# URL patterns for initiative, capability, and challenge detail views
urlpatterns += [
    path(
        "<str:product_slug>/initiative/<int:initiative_id>",
        InitiativeDetailView.as_view(),
        name="initiative_details",
    ),
    path(
        "<str:product_slug>/capability/<int:capability_id>",
        CapabilityDetailView.as_view(),
        name="capability_detail",
    ),
    path(
        "<str:product_slug>/challenge/<int:challenge_id>",
        ChallengeDetailView.as_view(),
        name="challenge_detail",
    ),
]
