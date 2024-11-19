from django.urls import path
from .views.base import PortalDashboardView, PortalUserSettingsView
from .views.product import (
    PortalProductListView,
    PortalProductSummaryView,
    PortalProductSettingsView,
    PortalManageUsersView,
    PortalAddProductUserView,
    PortalUpdateProductUserView,
    CreateProductView
)
from .views.work import (
    PortalBountyListView,
    PortalMyBountiesView,
    PortalChallengeListView,
    PortalBountyClaimView,
    BountyClaimActionView,
    PortalWorkReviewView
)
from .views.organisation import (
    OrganisationListView,
    OrganisationDetailView,
    OrganisationSettingsView,
    OrganisationMembersView,
    CreateOrganisationView,
    SwitchOrganisationView
)
from .views.product_tree import (
    ViewProductTreeView,
    CreateProductTreeView,
    EditProductTreeView,
    RefineProductTreeView,
    GenerateProductTreeView,
    SaveProductTreeView
)
from .views.agreement import (
    PortalAgreementTemplatesView,
    CreateAgreementTemplateView
)

app_name = 'portal'

urlpatterns = [
    # Dashboard
    path('', PortalDashboardView.as_view(), name='dashboard'),
    
    # User Profile/Settings
    path('settings/', PortalUserSettingsView.as_view(), name='user-settings'),
    
    # Product List
    path('products/', PortalProductListView.as_view(), name='products'),
    
    # Product-specific URLs
    path('product/<slug:product_slug>/', PortalProductSummaryView.as_view(), name='product-summary'),
    path('product/<slug:product_slug>/settings/', PortalProductSettingsView.as_view(), name='product-settings'),
    path('product/<slug:product_slug>/challenges/', PortalChallengeListView.as_view(), name='product-challenges'),
    path('product/<slug:product_slug>/challenges/filter/', PortalChallengeListView.as_view(), name='product-challenge-filter'),
    path('product/<slug:product_slug>/bounties/', PortalBountyListView.as_view(), name='product-bounties'),
    path('product/<slug:product_slug>/bounties/my/', PortalMyBountiesView.as_view(), name='product-my-bounties'),
    path('product/<slug:product_slug>/users/', PortalManageUsersView.as_view(), name='product-users'),
    path('product/<slug:product_slug>/users/add/', PortalAddProductUserView.as_view(), name='product-user-add'),
    path('product/<slug:product_slug>/review/', PortalWorkReviewView.as_view(), name='product-review'),
    path('product/<slug:product_slug>/agreements/', PortalAgreementTemplatesView.as_view(), name='product-agreements'),
    path('product/<slug:product_slug>/agreements/create/', CreateAgreementTemplateView.as_view(), name='create-agreement-template'),
    
    # Nested resources
    path('product/<slug:product_slug>/bounties/<int:pk>/claims/', PortalBountyClaimView.as_view(), name='product-bounty-claims'),
    path('product/<slug:product_slug>/bounties/<int:pk>/claims/<int:claim_id>/actions/', BountyClaimActionView.as_view(), name='product-bounty-claim-actions'),
    
    # Organisation management
    path('organisations/', OrganisationListView.as_view(), name='organisations'),
    path('organisations/<int:org_id>/', OrganisationDetailView.as_view(), name='organisation-detail'),
    path('organisations/<int:org_id>/switch/', SwitchOrganisationView.as_view(), name='switch-organisation'),
    path('organisations/<int:org_id>/settings/', OrganisationSettingsView.as_view(), name='organisation-settings'),
    path('organisations/<int:org_id>/members/', OrganisationMembersView.as_view(), name='organisation-members'),
    path('organisations/create/', CreateOrganisationView.as_view(), name='create-organisation'),
    path('organisations/<int:org_id>/products/create/', CreateProductView.as_view(), name='create-product'),
    
    # Product Tree URLs
    path('product/<slug:product_slug>/tree/', ViewProductTreeView.as_view(), name='view-product-tree'),
    path('product/<slug:product_slug>/tree/create/', CreateProductTreeView.as_view(), name='create-product-tree'),
    path('product/<slug:product_slug>/tree/edit/', EditProductTreeView.as_view(), name='edit-product-tree'),
    path('product/<slug:product_slug>/tree/refine/', RefineProductTreeView.as_view(), name='refine-product-tree'),
    path('product/<slug:product_slug>/tree/generate/', GenerateProductTreeView.as_view(), name='generate-product-tree'),
    path('product/<slug:product_slug>/tree/save/', SaveProductTreeView.as_view(), name='save-product-tree'),
    path('product/<slug:product_slug>/users/<int:user_id>/update/', 
         PortalUpdateProductUserView.as_view(), 
         name='product-user-update'),
]
