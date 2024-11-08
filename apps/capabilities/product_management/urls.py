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
    ProductPeopleView,
    CreateInitiativeView,
    InitiativeDetailView,
    redirect_challenge_to_bounties,
    CreateBountyView,
    DeleteBountyView,
    ContributorAgreementTemplateView,
    CreateContributorAgreementTemplateView,
    UpdateChallengeView,
    DeleteChallengeView,
    BountyDetailView,
    BountyClaimView,
    CreateProductView,
    UpdateProductView,
    CreateOrganisationView,
    ProductChallengesView,
    ChallengeDetailView,
    DeleteBountyClaimView,
    UpdateBountyView,
    ProductDetailView,
    ProductContributorsView,
)

from .views.ideas_and_bugs_views import (
    ProductIdeasAndBugsView,
    CreateProductIdea,
    UpdateProductIdea,
    ProductIdeaDetail,
    CreateProductBug,
    ProductBugDetail,
    UpdateProductBug,
    cast_vote_for_idea,
    ProductIdeaListView,
    ProductBugListView,
)

app_name = 'product_management'

# URL patterns for challenge and product list views
urlpatterns = [
    path("", ProductListView.as_view(), name="products"),
    path("bounties/", BountyListView.as_view(), name="bounty-list"),
    path("challenges/", redirect_challenge_to_bounties, name="challenges"),
    re_path(r"^challenges/.*$", redirect_challenge_to_bounties, name="challenges"),
    path(
        "<str:product_slug>/challenge/<int:pk>/",
        ChallengeDetailView.as_view(),
        name="challenge-detail",
    ),
    path(
        "<str:product_slug>/challenge/update/<int:pk>/",
        UpdateChallengeView.as_view(),
        name="update-challenge",
    ),
    path(
        "<str:product_slug>/challenge/delete/<int:pk>/",
        DeleteChallengeView.as_view(),
        name="delete-challenge",
    ),
    path(
        "<str:product_slug>/challenge/<int:challenge_id>/bounty/<int:pk>",
        BountyDetailView.as_view(),
        name="bounty-detail",
    ),
    path(
        "<str:product_slug>/challenge/<int:challenge_id>/bounty/create/",
        CreateBountyView.as_view(),
        name="create-bounty",
    ),
    path(
        "<str:product_slug>/challenge/<int:challenge_id>/bounty/delete/<int:pk>",
        DeleteBountyView.as_view(),
        name="delete-bounty",
    ),
    path(
        "bounty-claim/<int:pk>/",
        BountyClaimView.as_view(),
        name="bounty-claim",
    ),
    path(
        "create",
        CreateProductView.as_view(),
        name="create-product",
    ),
    path(
        "<int:pk>/update/",
        UpdateProductView.as_view(),
        name="update-product",
    ),
    path(
        "organisation/create",
        CreateOrganisationView.as_view(),
        name="create-organisation",
    ),
    path("<str:product_slug>/bounties/", ProductBountyListView.as_view(), name="product-bounties"),
]

# Product URLs
urlpatterns += [
    path(
        "<str:product_slug>/",
        ProductRedirectView.as_view(),
        name="product-detail",
    ),
    path(
        "<str:product_slug>/summary/",
        ProductSummaryView.as_view(),
        name="product-summary",
    ),
    path(
        "<str:product_slug>/initiatives",
        ProductInitiativesView.as_view(),
        name="product-initiatives",
    ),
    path(
        "<str:product_slug>/challenges",
        ProductChallengesView.as_view(),
        name="product-challenges",
    ),
    path(
        "bounties",
        ProductBountyListView.as_view(),
        name="product-bounties",
    ),
    path(
        "tree",
        ProductTreeInteractiveView.as_view(),
        name="product-tree",
    ),
    path(
        "product-areas",
        ProductAreaCreateView.as_view(),
        name="product-area",
    ),
    path(
        "product-areas/<int:pk>/update",
        ProductAreaUpdateView.as_view(),
        name="product-area-update",
    ),
    path(
        "product-areas/<int:pk>/detail",
        ProductAreaDetailView.as_view(),
        name="product-area-detail",
    ),
    path(
        "idea-list",
        ProductIdeaListView.as_view(),
        name="product-idea-list",
    ),
    path(
        "bug-list",
        ProductBugListView.as_view(),
        name="product-bug-list",
    ),
    path(
        "ideas-and-bugs",
        ProductIdeasAndBugsView.as_view(),
        name="product-ideas-bugs",
    ),
    path(
        "ideas/new",
        CreateProductIdea.as_view(),
        name="add-product-idea",
    ),
    path(
        "idea/<int:pk>",
        ProductIdeaDetail.as_view(),
        name="product-idea-detail",
    ),
    path(
        "ideas/update/<int:pk>",
        UpdateProductIdea.as_view(),
        name="update-product-idea",
    ),
    path(
        "bugs/new",
        CreateProductBug.as_view(),
        name="add-product-bug",
    ),
    path(
        "bug/<int:pk>",
        ProductBugDetail.as_view(),
        name="product-bug-detail",
    ),
    path(
        "bugs/update/<int:pk>",
        UpdateProductBug.as_view(),
        name="update-product-bug",
    ),
    path(
        "people",
        ProductPeopleView.as_view(),
        name="product-people",
    ),
    path(
        'ideas-bugs/',
        ProductIdeasAndBugsView.as_view(),
        name='product-ideas-bugs'
    ),
    path('<str:product_slug>/contributors/', ProductContributorsView.as_view(), name='product-contributors'),
]

# Initiative URLs
urlpatterns += [
    path(
        "<str:product_slug>/initiative/create",
        CreateInitiativeView.as_view(),
        name="create-initiative",
    ),
    path(
        "<str:product_slug>/initiative/<int:pk>",
        InitiativeDetailView.as_view(),
        name="initiative-detail",
    ),
]

# Contributor agreement URLs
urlpatterns += [
    path(
        "<str:product_slug>/contributor-agreement/<int:pk>",
        ContributorAgreementTemplateView.as_view(),
        name="contributor-agreement-template-detail",
    ),
    path(
        "<str:product_slug>/contributor-agreement/create/",
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

# Additional URLs
urlpatterns += [
    path(
        'delete/bounty/claim/',
        DeleteBountyClaimView.as_view(),
        name='delete-bounty-claim'
    ),
    path(
        'product/<slug:product_slug>/challenge/<int:challenge_id>/bounty/<int:bounty_id>/update/',
        UpdateBountyView.as_view(),
        name='update-bounty'
    ),
]

# Ideas and Bugs URLs
urlpatterns += [
    path('<str:product_slug>/ideas-and-bugs/', ProductIdeasAndBugsView.as_view(), name='ideas-and-bugs'),
    path('<str:product_slug>/ideas/create/', CreateProductIdea.as_view(), name='create-idea'),
    path('<str:product_slug>/ideas/', ProductIdeaListView.as_view(), name='idea-list'),
    path('<str:product_slug>/ideas/<int:pk>/', ProductIdeaDetail.as_view(), name='idea-detail'),
    path('<str:product_slug>/ideas/<int:pk>/update/', UpdateProductIdea.as_view(), name='update-idea'),
    path('<str:product_slug>/ideas/<int:pk>/vote/', cast_vote_for_idea, name='vote-idea'),
    
    path('<str:product_slug>/bugs/create/', CreateProductBug.as_view(), name='create-bug'),
    path('<str:product_slug>/bugs/', ProductBugListView.as_view(), name='bug-list'),
    path('<str:product_slug>/bugs/<int:pk>/', ProductBugDetail.as_view(), name='bug-detail'),
    path('<str:product_slug>/bugs/<int:pk>/update/', UpdateProductBug.as_view(), name='update-bug'),
]