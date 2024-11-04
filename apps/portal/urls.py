from django.urls import path
from .views import (
    PortalDashboardView,
    PortalProductListView,
    PortalProductDetailView,
    PortalProductSettingsView,
    PortalManageUsersView,
    PortalAddProductUserView,
    PortalUpdateProductUserView,
    PortalBountyListView,
    PortalBountyClaimView,
    PortalMyBountiesView,
    PortalChallengeListView,
    PortalWorkReviewView,
    PortalAgreementTemplatesView,
    bounty_claim_actions,
)

app_name = 'portal'

urlpatterns = [
    # Dashboard
    path('', PortalDashboardView.as_view(), name='dashboard'),
    
    # Product management
    path('products/<slug:slug>/', PortalProductDetailView.as_view(), name='product-detail'),
    path('products/<slug:slug>/settings/', PortalProductSettingsView.as_view(), name='product-settings'),
    
    # User management
    path('products/<slug:slug>/users/', PortalManageUsersView.as_view(), name='product-users'),
    path('products/<slug:slug>/users/add/', PortalAddProductUserView.as_view(), name='product-user-add'),
    path('products/<slug:slug>/users/<int:user_id>/', PortalUpdateProductUserView.as_view(), name='product-user-update'),
    
    # Bounty management
    path('products/<slug:slug>/bounties/', PortalBountyListView.as_view(), name='bounty-manage'),
    path('products/<slug:slug>/bounties/my/', PortalMyBountiesView.as_view(), name='my-bounties'),
    path('products/<slug:slug>/bounties/<int:pk>/claims/', PortalBountyClaimView.as_view(), name='bounty-claims'),
    
    # Challenge management
    path('products/<slug:slug>/challenges/', PortalChallengeListView.as_view(), name='challenge-manage'),
    
    # Work review
    path('products/<slug:slug>/work/review/', PortalWorkReviewView.as_view(), name='work-review'),
    
    # Agreements
    path('products/<slug:slug>/agreements/templates/', PortalAgreementTemplatesView.as_view(), name='agreement-templates'),
    
    # Add these URLs:
    path('products/', PortalProductListView.as_view(), name='products'),
    path('products/<slug:slug>/bounties/<int:pk>/claims/<int:claim_id>/actions/', 
         bounty_claim_actions, name='bounty-claim-actions'),
]
