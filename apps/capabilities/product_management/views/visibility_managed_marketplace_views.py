"""
Visibility Managed Views for Product-Talent Marketplace
=====================================================

This module contains views that enforce product visibility rules based on product settings
and user permissions.

Security Architecture
-------------------
Products have three visibility levels:
- GLOBAL: Visible to all users (authenticated or not)
- ORG_ONLY: Visible only to members of the associated organization
- RESTRICTED: Visible only to users with explicit ProductRoleAssignment

View Types and Visibility Enforcement
----------------------------------
1. Single-Product Views:
   - Use when displaying/managing one specific product
   - Inherit from ProductVisibilityCheckMixin
   - Implement get_product() to return the relevant Product instance
   - Mixin checks visibility rules for that specific product

2. Multi-Product Views:
   - Use when displaying items across multiple products (e.g., all bounties)
   - Use ProductService.get_visible_products() which:
     a. For anonymous users: returns only GLOBAL products
     b. For authenticated users: returns products that are either:
        - GLOBAL visibility
        - ORG_ONLY where user is a member
        - RESTRICTED where user has explicit access
        - Owned by the user
   - Filter your queryset using these visible products
"""


from django.views.generic import ListView, DetailView, TemplateView
from django.shortcuts import get_object_or_404
from django.db.models import Count
from itertools import groupby
from operator import attrgetter

from ..models import (
    Product, 
    Bounty, 
    Challenge, 
    Initiative, 
    ProductArea,
    ProductContributorAgreement,
    Idea,
    Bug
)
from .view_mixins import ProductVisibilityCheckMixin
from apps.capabilities.security.services import RoleService
from apps.capabilities.security.models import ProductRoleAssignment
from ..services import ProductService
from apps.capabilities.product_management.services import (
    ChallengeService,
    InitiativeService,
    ProductTreeService,
    ProductPeopleService,
    BountyService
)


class PublicBountyListView(ListView):
    """View for listing all public bounties across products"""
    model = Bounty
    template_name = "product_management/bounty/list.html"
    context_object_name = 'bounties'
    paginate_by = 20

    def get_queryset(self):
        return BountyService.get_visible_bounties(self.request.user)


class ProductBountyListView(ProductVisibilityCheckMixin, ListView):
    """View for listing bounties for a specific product"""
    model = Bounty
    template_name = "product_management/product_bounties.html"
    context_object_name = 'bounties'
    paginate_by = 20

    def get_product(self):
        return get_object_or_404(Product, slug=self.kwargs['product_slug'])

    def get_queryset(self):
        return BountyService.get_product_bounties(self.kwargs['product_slug'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.get_product()
        return context


class ProductSummaryView(ProductVisibilityCheckMixin, DetailView):
    """Public view for product summary"""
    model = Product
    template_name = "product_management/product_summary.html"
    slug_url_kwarg = 'product_slug'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product_slug'] = self.kwargs['product_slug']
        context['challenges'] = Challenge.objects.filter(product=self.object)
        return context


class ProductChallengesView(ProductVisibilityCheckMixin, DetailView):
    """Public view for product challenges"""
    model = Product
    template_name = 'product_management/product_challenges.html'
    slug_url_kwarg = 'product_slug'
    context_object_name = 'product'

    STATUS_COLORS = {
        'Draft': 'text-gray-500 border-gray-500',
        'Blocked': 'text-red-700 border-red-700',
        'Active': 'text-green-700 border-green-700',
        'Completed': 'text-blue-700 border-blue-700',
        'Cancelled': 'text-gray-400 border-gray-400',
    }
    
    def get_challenges_queryset(self):
        return Challenge.objects.filter(
            product=self.object
        ).select_related(
            'product_area',
            'created_by'
        ).prefetch_related(
            'bounty_set'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_person = self.request.user.person if self.request.user.is_authenticated else None
        
        context.update({
            'challenges': ChallengeService.get_product_challenges(self.object),
            'status_colors': self.STATUS_COLORS,
            'show_actions': current_person and RoleService.has_product_access(current_person, self.object),
            'can_modify': current_person and RoleService.has_product_management_access(current_person, self.object),
        })
        return context


class ProductInitiativesView(ProductVisibilityCheckMixin, ListView):
    """Public view for product initiatives"""
    model = Initiative
    template_name = "product_management/product_initiatives.html"
    context_object_name = 'initiatives'

    def get_product(self):
        return get_object_or_404(Product, slug=self.kwargs['product_slug'])

    def get_queryset(self):
        self.product = self.get_product()
        return InitiativeService.get_product_initiatives(self.product)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'product': self.product,
            'product_slug': self.kwargs['product_slug'],
            'can_manage': self.request.user.is_authenticated and RoleService.has_product_management_access(
                self.request.user.person, 
                self.product
            )
        })
        return context


class ProductTreeInteractiveView(ProductVisibilityCheckMixin, DetailView):
    """Public view for interactive product tree"""
    model = Product
    template_name = "product_management/product_tree.html"
    slug_url_kwarg = 'product_slug'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'tree_data': ProductTreeService.get_product_tree_data(self.object),
            'can_manage': self.request.user.is_authenticated and RoleService.has_product_management_access(
                self.request.user.person, 
                self.object
            )
        })
        return context


class ProductPeopleView(ProductVisibilityCheckMixin, ListView):
    """Public view for product people/contributors"""
    template_name = 'product_management/product_people.html'

    def get_product(self):
        return get_object_or_404(Product, slug=self.kwargs['product_slug'])

    def get_queryset(self):
        self.product = self.get_product()
        return ProductPeopleService.get_grouped_product_roles(self.product)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context.update({
            'product': self.product,
            'grouped_product_people': ProductPeopleService.get_grouped_product_roles(self.product)
        })
        return context 


class ProductListView(ListView):
    """View for listing all visible products"""
    model = Product
    template_name = "product_management/products.html"
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        # Use ProductService to get products visible to the current user
        return ProductService.get_visible_products(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['can_create'] = True  # Or any specific permission check
        return context


class ChallengeDetailView(ProductVisibilityCheckMixin, DetailView):
    """Public view for challenge details"""
    model = Challenge
    template_name = "product_management/challenge_detail.html"
    context_object_name = 'challenge'

    def get_product(self):
        return get_object_or_404(Product, slug=self.kwargs['product_slug'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.get_product()
        if self.request.user.is_authenticated:
            context['can_manage'] = RoleService.has_product_management_access(
                self.request.user.person,
                context['product']
            )
        return context


class ProductIdeasAndBugsView(ProductVisibilityCheckMixin, TemplateView):
    """Combined view for displaying both ideas and bugs for a product."""
    template_name = "product_management/product_ideas_and_bugs.html"

    def get_product(self):
        return get_object_or_404(Product, slug=self.kwargs['product_slug'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_product()
        context["product"] = product

        ideas = Idea.objects.filter(product=product)
        bugs = Bug.objects.filter(product=product)

        context.update({
            "ideas": ideas,
            "bugs": bugs,
        })
        return context


class ProductIdeaListView(ProductVisibilityCheckMixin, ListView):
    """View for listing ideas for a product."""
    model = Idea
    template_name = "product_management/product_idea_list.html"
    context_object_name = "ideas"

    def get_product(self):
        return get_object_or_404(Product, slug=self.kwargs['product_slug'])

    def get_queryset(self):
        return self.model.objects.filter(product=self.get_product())


class ProductBugListView(ProductVisibilityCheckMixin, ListView):
    """View for listing bugs for a product."""
    model = Bug
    template_name = "product_management/product_bug_list.html"
    context_object_name = "bugs"

    def get_product(self):
        return get_object_or_404(Product, slug=self.kwargs['product_slug'])

    def get_queryset(self):
        return self.model.objects.filter(product=self.get_product())


class ProductIdeaDetail(ProductVisibilityCheckMixin, DetailView):
    """Detail view for a product idea."""
    template_name = "product_management/product_idea_detail.html"
    model = Idea
    context_object_name = "idea"

    def get_product(self):
        return self.get_object().product

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "pk": self.object.pk,
        })

        if self.request.user.is_authenticated:
            context.update({
                "actions_available": self.object.person == self.request.user.person,
            })
        else:
            context.update({"actions_available": False})

        return context


class ProductBugDetail(ProductVisibilityCheckMixin, DetailView):
    """Detail view for a product bug."""
    template_name = "product_management/product_bug_detail.html"
    model = Bug
    context_object_name = "bug"

    def get_product(self):
        return self.get_object().product

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "pk": self.object.pk,
        })

        if self.request.user.is_authenticated:
            context.update({
                "actions_available": self.object.person == self.request.user.person,
            })
        else:
            context.update({"actions_available": False})

        return context


class BountyDetailView(ProductVisibilityCheckMixin, DetailView):
    """Public view for bounty details"""
    model = Bounty
    template_name = "product_management/bounty_detail.html"
    context_object_name = 'bounty'
    pk_url_kwarg = 'pk'

    def get_object(self):
        print("\nDEBUG: BountyDetailView.get_object()")
        print(f"URL kwargs: {self.kwargs}")
        
        try:
            bounty = Bounty.objects.select_related(
                'challenge', 
                'challenge__product'
            ).get(pk=self.kwargs['pk'])
            
            print(f"Found bounty: {bounty.id}")
            print(f"Challenge ID: {bounty.challenge.id}")
            print(f"Product: {bounty.challenge.product.name}")
            
            return bounty
        except Bounty.DoesNotExist as e:
            print(f"ERROR: Bounty not found: {e}")
            raise
        except Exception as e:
            print(f"ERROR: Unexpected error: {e}")
            raise

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bounty = self.get_object()
        
        # Package everything in a 'data' dict to match template expectations
        context['data'] = {
            'product': bounty.challenge.product,
            'challenge': bounty.challenge,
            'bounty': bounty,
            'show_actions': self.request.user.is_authenticated and RoleService.has_product_management_access(
                self.request.user.person,
                bounty.challenge.product
            )
        }
        
        # Add expertise list if needed
        context['expertise_list'] = []  # Add actual expertise list here if you have one
        
        return context