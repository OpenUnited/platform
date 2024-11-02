from django.urls import path, re_path, include

from .views.product_views import (
    ProductListView,
    ProductRedirectView,
    ProductSummaryView,
    ProductInitiativesView,
    ProductChallengesView,
    BountyListView,
    ProductBountyListView,
    ProductTreeInteractiveView,
    ProductAreaCreateView,
    ProductAreaUpdateView,
    ProductAreaDetailView,
    ProductRoleAssignmentView,
    CreateInitiativeView,
    InitiativeDetailView,
    redirect_challenge_to_bounties,
    UpdateChallengeView,
    DeleteChallengeView,
    BountyDetailView,
    CreateBountyView,
    UpdateBountyView,
    DeleteBountyView,
    BountyClaimView,
    CreateProductView,
    UpdateProductView,
    CreateOrganisationView,
    ContributorAgreementTemplateView,
    CreateContributorAgreementTemplateView,
    get_expertise,
)

from .views.portal_views import (
    PortalDashboardView,
    PortalManageBountiesView,
    PortalBountyClaimRequestsView,
    PortalProductDetailView,
    PortalProductChallengesView,
    PortalProductChallengeFilterView,
    PortalProductBountiesView,
    PortalProductBountyFilterView,
    PortalReviewWorkView,
    PortalContributorAgreementTemplateListView,
    PortalManageUsersView,
    PortalAddProductUserView,
    PortalUpdateProductUserView,
    PortalProductSettingView,
    DeleteBountyClaimView,
    bounty_claim_actions,
)

from .views.ideas_and_bugs_views import (
    ProductIdeasAndBugsView,
    ProductIdeaListView,
    ProductBugListView,
    CreateProductIdea,
    UpdateProductIdea,
    ProductIdeaDetail,
    CreateProductBug,
    ProductBugDetail,
    UpdateProductBug,
    cast_vote_for_idea,
)

# URL patterns for challenge and product list views
urlpatterns = [
    re_path(r"^challenges/.*$", redirect_challenge_to_bounties, name="challenges"),
    path("products/", ProductListView.as_view(), name="products"),
    path(
        "product/<str:product_slug>/challenge/update/<int:pk>/",
        UpdateChallengeView.as_view(),
        name="update-challenge",
    ),
    path(
        "product/<str:product_slug>/challenge/delete/<int:pk>/",
        DeleteChallengeView.as_view(),
        name="delete-challenge",
    ),
    path(
        "product/<str:product_slug>/challenge/<int:challenge_id>/bounty/<int:pk>",
        BountyDetailView.as_view(),
        name="bounty-detail",
    ),
    path(
        "product/<str:product_slug>/challenge/<int:challenge_id>/bounty/create/",
        CreateBountyView.as_view(),
        name="create-bounty",
    ),
    path(
        "product/<str:product_slug>/challenge/<int:challenge_id>/bounty/update/<int:pk>",
        UpdateBountyView.as_view(),
        name="update-bounty",
    ),
    path(
        "product/<str:product_slug>/challenge/<int:challenge_id>/bounty/delete/<int:pk>",
        DeleteBountyView.as_view(),
        name="delete-bounty",
    ),
    path(
        "bounty-claim/delete/<int:pk>",
        DeleteBountyClaimView.as_view(),
        name="delete-bounty-claim",
    ),
    path(
        "bounty-claim/<int:pk>/",
        BountyClaimView.as_view(),
        name="bounty-claim",
    ),
    path(
        "product/create",
        CreateProductView.as_view(),
        name="create-product",
    ),
    path(
        "product/<int:pk>/update/",
        UpdateProductView.as_view(),
        name="update-product",
    ),
    path(
        "organisation/create",
        CreateOrganisationView.as_view(),
        name="create-organisation",
    ),
]

# Portal URLs (renamed from Dashboard URLs)
urlpatterns += [
    path("portal/", PortalDashboardView.as_view(), name="portal-dashboard"),
    path(
        "portal/product/<str:product_slug>/<int:default_tab>/",
        PortalDashboardView.as_view(),
        name="portal-product-dashboard",
    ),
    path(
        "portal/bounties/",
        PortalManageBountiesView.as_view(),
        name="portal-manage-bounties",
    ),
    path(
        "portal/bounties/bounty-requests",
        PortalBountyClaimRequestsView.as_view(),
        name="portal-bounty-requests",
    ),
    path(
        "portal/product/<str:product_slug>/tab/<int:default_tab>/",
        PortalProductDetailView.as_view(),
        name="portal-product-detail",
    ),
    path(
        "portal/product/<str:product_slug>/challenges/",
        PortalProductChallengesView.as_view(),
        name="portal-product-challenges",
    ),
    path(
        "portal/product/<str:product_slug>/challenges/filter/",
        PortalProductChallengeFilterView.as_view(),
        name="portal-product-challenge-filter",
    ),
    path(
        "portal/product/<str:product_slug>/bounties/",
        PortalProductBountiesView.as_view(),
        name="portal-product-bounties",
    ),
    path(
        "portal/bounties/action/<int:pk>/",
        bounty_claim_actions,
        name="portal-bounties-action",
    ),
    path(
        "portal/product/<str:product_slug>/bounties/filter/",
        PortalProductBountyFilterView.as_view(),
        name="portal-product-bounty-filter",
    ),
    path(
        "portal/product/<str:product_slug>/review-work",
        PortalReviewWorkView.as_view(),
        name="portal-review-work",
    ),
    path(
        "portal/product/<str:product_slug>/contributor-agreement-templates",
        PortalContributorAgreementTemplateListView.as_view(),
        name="portal-contributor-agreement-templates",
    ),
    path(
        "portal/product/<str:product_slug>/user-management",
        PortalManageUsersView.as_view(),
        name="portal-manage-users",
    ),
    path(
        "portal/product/<str:product_slug>/add-product-user",
        PortalAddProductUserView.as_view(),
        name="portal-add-product-user",
    ),
    path(
        "portal/product/<str:product_slug>/product-users/<int:pk>/update",
        PortalUpdateProductUserView.as_view(),
        name="portal-update-product-user",
    ),
    path(
        "portal/product-setting/<int:pk>/",
        PortalProductSettingView.as_view(),
        name="portal-product-setting",
    ),
]

# Product URLs
urlpatterns += [
    path(
        "product/<str:product_slug>/",
        ProductRedirectView.as_view(),
        name="product-detail",
    ),
    path(
        "product/<str:product_slug>/summary/",
        ProductSummaryView.as_view(),
        name="product-summary",
    ),
    path(
        "product/<str:product_slug>/initiatives",
        ProductInitiativesView.as_view(),
        name="product-initiatives",
    ),
    path(
        "product/<str:product_slug>/challenges",
        ProductChallengesView.as_view(),
        name="product-challenges",
    ),
    path("bounties", BountyListView.as_view(), name="bounties"),
    path(
        "product/<str:product_slug>/bounties",
        ProductBountyListView.as_view(),
        name="product-bounties",
    ),
    path(
        "product/<str:product_slug>/tree",
        ProductTreeInteractiveView.as_view(),
        name="product-tree",
    ),
    path(
        "product/<str:product_slug>/product-areas",
        ProductAreaCreateView.as_view(),
        name="product-area",
    ),
    path(
        "product/<str:product_slug>/product-areas/<int:pk>/update",
        ProductAreaUpdateView.as_view(),
        name="product-area-update",
    ),
    path(
        "product/<str:product_slug>/product-areas/<int:pk>/detail",
        ProductAreaDetailView.as_view(),
        name="product-area-detail",
    ),
    path(
        "product/<str:product_slug>/idea-list",
        ProductIdeaListView.as_view(),
        name="product-idea-list",
    ),
    path(
        "product/<str:product_slug>/bug-list",
        ProductBugListView.as_view(),
        name="product-bug-list",
    ),
    path(
        "product/<str:product_slug>/ideas-and-bugs",
        ProductIdeasAndBugsView.as_view(),
        name="product-ideas-bugs",
    ),
    path(
        "product/<str:product_slug>/ideas/new",
        CreateProductIdea.as_view(),
        name="add-product-idea",
    ),
    path(
        "product/<str:product_slug>/idea/<int:pk>",
        ProductIdeaDetail.as_view(),
        name="product-idea-detail",
    ),
    path(
        "product/<str:product_slug>/ideas/update/<int:pk>",
        UpdateProductIdea.as_view(),
        name="update-product-idea",
    ),
    path(
        "product/<str:product_slug>/bugs/new",
        CreateProductBug.as_view(),
        name="add-product-bug",
    ),
    path(
        "product/<str:product_slug>/bug/<int:pk>",
        ProductBugDetail.as_view(),
        name="product-bug-detail",
    ),
    path(
        "product/<str:product_slug>/bugs/update/<int:pk>",
        UpdateProductBug.as_view(),
        name="update-product-bug",
    ),
    path(
        "product/<str:product_slug>/people",
        ProductRoleAssignmentView.as_view(),
        name="product-people",
    ),
]

# Initiative URLs
urlpatterns += [
    path(
        "product/<str:product_slug>/initiative/create",
        CreateInitiativeView.as_view(),
        name="create-initiative",
    ),
    path(
        "product/<str:product_slug>/initiative/<int:pk>",
        InitiativeDetailView.as_view(),
        name="initiative-detail",
    ),
]

# Contributor agreement URLs
urlpatterns += [
    path(
        "product/<str:product_slug>/contributor-agreement/<int:pk>",
        ContributorAgreementTemplateView.as_view(),
        name="contributor-agreement-template-detail",
    ),
    path(
        "product/<str:product_slug>/contributor-agreement/create/",
        CreateContributorAgreementTemplateView.as_view(),
        name="create-contributor-agreement-template",
    ),
]

# Voting URLs
urlpatterns += [
    path(
        "cast-vote-for-idea/<int:pk>",
        cast_vote_for_idea,
        name="cast-vote-for-idea",
    )
]

# Expertise URLs
urlpatterns += [
    path('get-expertise/', get_expertise, name='get-expertise'),
]

# Challenge authoring flow
urlpatterns += [
    path('product/<str:product_slug>/flows/challenge-authoring/', 
         include('product_management.flows.challenge_authoring.urls')),
]
