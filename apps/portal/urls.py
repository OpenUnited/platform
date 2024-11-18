from django.urls import path
from . import views

app_name = 'portal'

urlpatterns = [
    # Dashboard
    path('', views.PortalDashboardView.as_view(), name='dashboard'),
    
    # User Profile/Settings
    path('settings/', views.PortalUserSettingsView.as_view(), name='user-settings'),
    
    # Product List
    path('products/', views.PortalProductListView.as_view(), name='products'),
    
    # Product-specific URLs - all under /product/<product_slug>/
    path('product/<slug:product_slug>/', views.PortalProductSummaryView.as_view(), name='product-summary'),
    path('product/<slug:product_slug>/settings/', views.PortalProductSettingsView.as_view(), name='product-settings'),
    path('product/<slug:product_slug>/challenges/', views.PortalChallengeListView.as_view(), name='product-challenges'),
    path('product/<slug:product_slug>/challenges/filter/', 
         views.PortalChallengeListView.as_view(), 
         name='product-challenge-filter'),
    path('product/<slug:product_slug>/bounties/', views.PortalBountyListView.as_view(), name='product-bounties'),
    path('product/<slug:product_slug>/bounties/my/', views.PortalMyBountiesView.as_view(), name='product-my-bounties'),
    path('product/<slug:product_slug>/users/', views.PortalManageUsersView.as_view(), name='product-users'),
    path('product/<slug:product_slug>/users/add/', views.PortalAddProductUserView.as_view(), name='product-user-add'),
    path('product/<slug:product_slug>/review/', views.PortalWorkReviewView.as_view(), name='product-review'),
    path('product/<slug:product_slug>/agreements/', views.PortalAgreementTemplatesView.as_view(), name='product-agreements'),
    path('product/<slug:product_slug>/agreements/create/',
         views.CreateAgreementTemplateView.as_view(),
         name='create-agreement-template'),
    
    # Nested resources
    path('product/<slug:product_slug>/bounties/<int:pk>/claims/', 
         views.PortalBountyClaimView.as_view(), name='product-bounty-claims'),
    path('product/<slug:product_slug>/users/<int:user_id>/',
         views.PortalUpdateProductUserView.as_view(), name='product-user-update'),
    path('product/<slug:product_slug>/bounties/<int:pk>/claims/<int:claim_id>/actions/',
         views.BountyClaimActionView.as_view(), name='product-bounty-claim-actions'),
    
    # Organisation management
    path('organisations/', 
         views.OrganisationListView.as_view(), 
         name='organisations'),
    path('organisations/<int:org_id>/', 
         views.OrganisationDetailView.as_view(), 
         name='organisation-detail'),
    path('organisations/<int:org_id>/switch/', 
         views.SwitchOrganisationView.as_view(), 
         name='switch-organisation'),
    path('organisations/<int:org_id>/settings/', 
         views.OrganisationSettingsView.as_view(), 
         name='organisation-settings'),
    path('organisations/<int:org_id>/members/', 
         views.OrganisationMembersView.as_view(), 
         name='organisation-members'),
    path('organisations/create/', 
         views.CreateOrganisationView.as_view(), 
         name='create-organisation'),
    path('organisations/<int:org_id>/products/create/', 
         views.CreateProductView.as_view(), 
         name='create-product'),
    
    # Product Tree URLs
    path('product/<slug:product_slug>/tree/', 
         views.ViewProductTreeView.as_view(), 
         name='view-product-tree'),
    path('product/<slug:product_slug>/tree/create/', 
         views.CreateProductTreeView.as_view(), 
         name='create-product-tree'),
    path('product/<slug:product_slug>/tree/edit/', 
         views.EditProductTreeView.as_view(), 
         name='edit-product-tree'),
    path('product/<slug:product_slug>/tree/refine/', 
         views.RefineProductTreeView.as_view(), 
         name='refine-product-tree'),
    # API endpoints
    path('product/<slug:product_slug>/tree/generate/', 
         views.GenerateProductTreeView.as_view(), 
         name='generate-product-tree'),
    path('product/<slug:product_slug>/tree/save/', 
         views.SaveProductTreeView.as_view(), 
         name='save-product-tree'),
]
