from django.urls import path, re_path

from . import views

# Developer's Note: I separated the urlpatterns because I found it convenient to do like this.
# It looked too ugly when putting every path into a single list.
#
# If a new path requires to be added, add it to their corresponding part. If it does not fit
# any of the existing groups, you can add an additional group.


# URL patterns for challenge and product list views
urlpatterns = [
    # This pattern matches any subpath under 'challenges/'
    re_path(r"^challenges/.*$", views.redirect_challenge_to_bounties, name="challenges"),
    path(
        "<str:product_slug>/challenge/create/",
        views.CreateChallengeView.as_view(),
        name="create-challenge",
    ),
    path(
        "<str:product_slug>/challenge/update/<int:pk>/",
        views.UpdateChallengeView.as_view(),
        name="update-challenge",
    ),
    path(
        "<str:product_slug>/challenge/delete/<int:pk>/",
        views.DeleteChallengeView.as_view(),
        name="delete-challenge",
    ),
    path(
        "<str:product_slug>/challenge/<int:challenge_id>/bounty/<int:pk>",
        views.BountyDetailView.as_view(),
        name="bounty-detail",
    ),
    path(
        "<str:product_slug>/challenge/<int:challenge_id>/bounty/create/",
        views.CreateBountyView.as_view(),
        name="create-bounty",
    ),
    path(
        "<str:product_slug>/challenge/<int:challenge_id>/bounty/update/<int:pk>",
        views.UpdateBountyView.as_view(),
        name="update-bounty",
    ),
    path(
        "<str:product_slug>/challenge/<int:challenge_id>/bounty/delete/<int:pk>",
        views.DeleteBountyView.as_view(),
        name="delete-bounty",
    ),
    path(
        "bounty_claim/delete/<int:pk>",
        views.DeleteBountyClaimView.as_view(),
        name="delete-bounty-claim",
    ),
    path("products/", views.ProductListView.as_view(), name="products"),
    path(
        "bounty-claim/<int:pk>/",
        views.BountyClaimView.as_view(),
        name="bounty-claim",
    ),
    path(
        "product/create",
        views.CreateProductView.as_view(),
        name="create-product",
    ),
    path(
        "product/update/<int:pk>/",
        views.UpdateProductView.as_view(),
        name="update-product",
    ),
    path(
        "organisation/create",
        views.CreateOrganisationView.as_view(),
        name="create-organisation",
    ),
]

urlpatterns += [
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path(
        "dashboard/home",
        views.DashboardHomeView.as_view(),
        name="dashboard-home",
    ),
    path(
        "dashboard/bounties",
        views.ManageBountiesView.as_view(),
        name="manage-bounties",
    ),
    path(
        "dashboard/bounties/bounty-requests",
        views.DashboardBountyClaimRequestsView.as_view(),
        name="dashboard-bounty-requests",
    ),
    path(
        "dashboard/product/<str:product_slug>/",
        views.DashboardProductDetailView.as_view(),
        name="dashboard-product-detail",
    ),
    path(
        "dashboard/product/<str:product_slug>/challenges/",
        views.DashboardProductChallengesView.as_view(),
        name="dashboard-product-challenges",
    ),
    path(
        "dashboard/product/<str:product_slug>/challenges/filter/",
        views.DashboardProductChallengeFilterView.as_view(),
        name="dashboard-product-challenge-filter",
    ),
    path(
        "dashboard/product/<str:product_slug>/bounties/",
        views.DashboardProductBountiesView.as_view(),
        name="dashboard-product-bounties",
    ),
    path(
        "dashboard/bounties/action/<int:pk>/",
        views.bounty_claim_actions,
        name="dashboard-bounties-action",
    ),
    path(
        "dashboard/product/<str:product_slug>/bounties/filter/",
        views.DashboardProductBountyFilterView.as_view(),
        name="dashboard-product-bounty-filter",
    ),
    path(
        "dashboard/product/<str:product_slug>/review-work",
        views.DashboardReviewWorkView.as_view(),
        name="dashboard-review-work",
    ),
    path(
        "dashboard/product/<str:product_slug>/contributor-agreement-templates",
        views.DashboardContributorAgreementTemplateListView.as_view(),
        name="dashboard-contributor-agreement-templates",
    ),
    path(
        "dashboard/product/<str:product_slug>/user-management",
        views.ManageUsersView.as_view(),
        name="manage-users",
    ),
    path(
        "dashboard/product/<str:product_slug>/add-product-user",
        views.AddProductUserView.as_view(),
        name="add-product-user",
    ),
    path(
        "dashboard/product/<str:product_slug>/product-users/<int:pk>/update",
        views.UpdateProductUserView.as_view(),
        name="update-product-user",
    ),
]


# URL patterns for contributor agreement views
urlpatterns += [
    path(
        "<str:product_slug>/contributor-agreement/<int:pk>",
        views.ContributorAgreementTemplateView.as_view(),
        name="contributor-agreement-template-detail",
    ),
    path(
        "<str:product_slug>/contributor-agreement/create/",
        views.CreateContributorAgreementTemplateView.as_view(),
        name="create-contributor-agreement-template",
    ),
    # path(
    #     "<str:product_slug>/contribution-agreement/update/<int:pk>",
    #     views.UpdateContributionAgreementView.as_view(),
    #     name="update-contribution-agreement",
    # ),
]


# URL patterns for various product views
urlpatterns += [
    path(
        "product/<str:product_slug>/",
        views.ProductRedirectView.as_view(),
        name="product_detail",
    ),
    path(
        "<str:product_slug>/summary",
        views.ProductSummaryView.as_view(),
        name="product_summary",
    ),
    path(
        "<str:product_slug>/initiatives",
        views.ProductInitiativesView.as_view(),
        name="product_initiatives",
    ),
    path(
        "<str:product_slug>/challenges",
        views.ProductChallengesView.as_view(),
        name="product_challenges",
    ),
    path("bounties", views.BountyListView.as_view(), name="bounties"),
    path(
        "<str:product_slug>/bounties",
        views.ProductBountyListView.as_view(),
        name="product_bounties",
    ),
    path(
        "<str:product_slug>/tree",
        views.ProductTreeInteractiveView.as_view(),
        name="product_tree",
    ),
    path(
        "<str:product_slug>/product-areas",
        views.ProductAreaCreateView.as_view(),
        name="product_area",
    ),
    path(
        "<str:product_slug>/product-areas/<int:pk>/update",
        views.ProductAreaUpdateView.as_view(),
        name="product_area_update",
    ),
    path(
        "<str:product_slug>/product-areas/<int:pk>/detail",
        views.ProductAreaDetailView.as_view(),
        name="product_area_detail",
    ),
    path(
        "<str:product_slug>/idea-list",
        views.ProductIdeaListView.as_view(),
        name="product_idea_list",
    ),
    path(
        "<str:product_slug>/bug-list",
        views.ProductBugListView.as_view(),
        name="product_bug_list",
    ),
    path(
        "<str:product_slug>/ideas-and-bugs",
        views.ProductIdeasAndBugsView.as_view(),
        name="product_ideas_bugs",
    ),
    path(
        "<str:product_slug>/ideas/new",
        views.CreateProductIdea.as_view(),
        name="add_product_idea",
    ),
    path(
        "<str:product_slug>/idea/<int:pk>",
        views.ProductIdeaDetail.as_view(),
        name="product_idea_detail",
    ),
    path(
        "<str:product_slug>/ideas/update/<int:pk>",
        views.UpdateProductIdea.as_view(),
        name="update_product_idea",
    ),
    path(
        "<str:product_slug>/bugs/new",
        views.CreateProductBug.as_view(),
        name="add_product_bug",
    ),
    path(
        "<str:product_slug>/bug/<int:pk>",
        views.ProductBugDetail.as_view(),
        name="product_bug_detail",
    ),
    path(
        "<str:product_slug>/bugs/update/<int:pk>",
        views.UpdateProductBug.as_view(),
        name="update_product_bug",
    ),
    path(
        "<str:product_slug>/people",
        views.ProductRoleAssignmentView.as_view(),
        name="product_people",
    ),
]

# URL patterns for initiative, capability, and challenge detail views
urlpatterns += [
    path(
        "<str:product_slug>/initiative/create",
        views.CreateInitiativeView.as_view(),
        name="create-initiative",
    ),
    path(
        "<str:product_slug>/initiative/<int:pk>",
        views.InitiativeDetailView.as_view(),
        name="initiative_detail",
    ),
    path(
        "<str:product_slug>/capability/create",
        views.CreateCapability.as_view(),
        name="create-capability",
    ),
    path(
        "<str:product_slug>/capability/<int:pk>",
        views.CapabilityDetailView.as_view(),
        name="capability_detail",
    ),
    path(
        "<str:product_slug>/challenge/<int:pk>",
        views.ChallengeDetailView.as_view(),
        name="challenge_detail",
    ),
]


urlpatterns += [
    path(
        "cast-vote-for-idea/<int:pk>",
        views.cast_vote_for_idea,
        name="cast-vote-for-idea",
    )
]
