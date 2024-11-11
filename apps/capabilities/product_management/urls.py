from django.urls import path, re_path
from django.views.generic import RedirectView

from .views.visibility_managed_marketplace_views import (
    PublicBountyListView,
    ProductBountyListView,
    ProductSummaryView,
    ProductInitiativesView,
    ProductChallengesView,
    ProductTreeInteractiveView,
    ProductPeopleView,
    ProductListView,
    BountyDetailView,
    ChallengeDetailView,
    ProductIdeasAndBugsView,
    ProductIdeaListView,
    ProductBugListView,
    ProductIdeaDetail,
    ProductBugDetail,
)

from .views.authenticated_marketplace_views import (
    ProductAreaCreateView,
    ProductAreaUpdateView,
    ProductAreaDetailView,
    CreateInitiativeView,
    InitiativeDetailView,
    CreateBountyView,
    DeleteBountyView,
    ContributorAgreementTemplateView,
    CreateContributorAgreementTemplateView,
    UpdateChallengeView,
    DeleteChallengeView,
    BountyClaimView,
    CreateProductView,
    UpdateProductView,
    CreateOrganisationView,
    DeleteBountyClaimView,
    UpdateBountyView,
    CreateProductIdea,
    UpdateProductIdea,
    CreateProductBug,
    UpdateProductBug,
    cast_vote_for_idea,
)

app_name = 'product_management'

# Visibility Manage routes - no login required, visibility controlled by ProductVisibilityCheckMixin
urlpatterns = [
    path("bounties/", PublicBountyListView.as_view(), name="bounty-list"),
    path("<str:product_slug>/challenge/<int:challenge_id>/bounty/<int:pk>/", BountyDetailView.as_view(), name="bounty-detail"),
    path("<str:product_slug>/bounties/", ProductBountyListView.as_view(), name="product-bounties"),
    path("<str:product_slug>/summary/", ProductSummaryView.as_view(), name="product-summary"),
    path("<str:product_slug>/initiatives/", ProductInitiativesView.as_view(), name="product-initiatives"),
    path("<str:product_slug>/challenges/", ProductChallengesView.as_view(), name="product-challenges"),
    path("<str:product_slug>/tree/", ProductTreeInteractiveView.as_view(), name="product-tree"),
    path("<str:product_slug>/people/", ProductPeopleView.as_view(), name="product-people"),
    path("<str:product_slug>/ideas-and-bugs/", ProductIdeasAndBugsView.as_view(), name="product-ideas-bugs"),
    path("<str:product_slug>/ideas/", ProductIdeaListView.as_view(), name="product-ideas"),
    path("<str:product_slug>/bugs/", ProductBugListView.as_view(), name="product-bugs"),
    path("<str:product_slug>/idea/<int:pk>/", ProductIdeaDetail.as_view(), name="product-idea-detail"),
    path("<str:product_slug>/bug/<int:pk>/", ProductBugDetail.as_view(), name="product-bug-detail"),
]

# Authenticated routes - require login and proper permissions
urlpatterns += [
    path("", ProductListView.as_view(), name="products"),
    path("create/", CreateProductView.as_view(), name="create-product"),
    path("<int:pk>/update/", UpdateProductView.as_view(), name="update-product"),
    path("organisation/create/", CreateOrganisationView.as_view(), name="create-organisation"),
    
    # Product Areas
    path("product-areas/", ProductAreaCreateView.as_view(), name="product-area"),
    path("product-areas/<int:pk>/update/", ProductAreaUpdateView.as_view(), name="product-area-update"),
    path("product-areas/<int:pk>/detail/", ProductAreaDetailView.as_view(), name="product-area-detail"),
    
    # Challenges and Bounties
    path("<str:product_slug>/challenge/<int:pk>/", ChallengeDetailView.as_view(), name="challenge-detail"),
    path("<str:product_slug>/challenge/update/<int:pk>/", UpdateChallengeView.as_view(), name="update-challenge"),
    path("<str:product_slug>/challenge/delete/<int:pk>/", DeleteChallengeView.as_view(), name="delete-challenge"),
    path("<str:product_slug>/challenge/<int:challenge_id>/bounty/create/", CreateBountyView.as_view(), name="create-bounty"),
    path("<str:product_slug>/challenge/<int:challenge_id>/bounty/delete/<int:pk>/", DeleteBountyView.as_view(), name="delete-bounty"),
    path("<str:product_slug>/challenge/<int:challenge_id>/bounty/<int:bounty_id>/update/", UpdateBountyView.as_view(), name="update-bounty"),
    path("bounty-claim/<int:pk>/", BountyClaimView.as_view(), name="bounty-claim"),
    path("delete/bounty/claim/", DeleteBountyClaimView.as_view(), name="delete-bounty-claim"),
    
    # Initiatives
    path("<str:product_slug>/initiative/create/", CreateInitiativeView.as_view(), name="create-initiative"),
    path("<str:product_slug>/initiative/<int:pk>/", InitiativeDetailView.as_view(), name="initiative-detail"),
    
    # Contributor Agreements
    path("<str:product_slug>/contributor-agreement/<int:pk>/", ContributorAgreementTemplateView.as_view(), name="contributor-agreement-template-detail"),
    path("<str:product_slug>/contributor-agreement/create/", CreateContributorAgreementTemplateView.as_view(), name="create-contributor-agreement-template"),

    path("<str:product_slug>/idea/create/", CreateProductIdea.as_view(), name="create-idea"),
    path("<str:product_slug>/idea/<int:pk>/update/", UpdateProductIdea.as_view(), name="update-idea"),
    path("<str:product_slug>/bug/create/", CreateProductBug.as_view(), name="create-bug"),
    path("<str:product_slug>/bug/<int:pk>/update/", UpdateProductBug.as_view(), name="update-bug"),
    path("idea/<int:pk>/vote/", cast_vote_for_idea, name="cast-vote-for-idea"),
]

urlpatterns += [
    path('products/<slug:product_slug>/agreement-template/create/', 
         CreateContributorAgreementTemplateView.as_view(), 
         name='create-agreement-template'),
    
    path('ideas/<int:pk>/vote/', 
         cast_vote_for_idea, 
         name='cast-vote'),
]