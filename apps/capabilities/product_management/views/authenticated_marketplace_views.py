"""
Authenticated Marketplace Views for Product Management
==================================================

This module contains views that require authentication and handle product management
operations. These views enforce both authentication and product-specific management
permissions.

Security Architecture
-------------------
All views in this module require authentication through Django's LoginRequiredMixin
or the custom BaseProductView. Access control is implemented at two levels:

1. Authentication Level:
   - All views require a logged-in user
   - Unauthenticated requests are redirected to the login page

2. Product Management Level:
   - Product-specific views check management permissions via RoleService
   - Users must have explicit product management access for operations
   - Access is verified in BaseProductView.dispatch()

View Categories
-------------
1. Product Management Views:
   - Create, update, and manage product details
   - Restricted to users with product management permissions

2. Contributor Agreement Views:
   - Manage templates and agreements for product contributors
   - Typically restricted to product owners/managers

3. Organization Views:
   - Create and manage product-related organizations
   - Limited to authorized organization managers

4. Product Structure Views:
   - Manage product areas, initiatives, and challenges
   - Requires product management access

5. Bounty Management Views:
   - Create, update, and manage product bounties
   - Control bounty claims and rewards
   - Restricted to product managers

6. Ideas and Bugs Views:
   - Manage product feedback and issue tracking
   - May have different permission levels for creation vs management

Permission Enforcement
--------------------
- BaseProductView handles common authentication and permission checks
- RoleService.has_product_management_access() verifies management permissions
- Product ownership and organization membership are considered for access control
"""

import logging
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, AccessMixin
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    UpdateView,
    View,
    FormView
)
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.views.generic.detail import SingleObjectMixin
from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.utils.decorators import method_decorator

from apps.capabilities.product_management.services import IdeaService, ProductService, ProductManagementService, ContributorAgreementService
from ..forms import IdeaForm, BugForm
from ..models import Idea, Bug, IdeaVote

from apps.capabilities.security.services import RoleService
from apps.common import mixins as common_mixins
from ..forms import (
    BountyForm,
    ContributorAgreementTemplateForm,
    OrganisationForm,
    ChallengeForm,
    ProductAreaForm,
    ProductForm,
    InitiativeForm
)
from ..models import (
    Bounty,
    Challenge,
    Initiative,
    Product,
    ProductArea,
    ProductContributorAgreement,
    ProductContributorAgreementTemplate,
)

from apps.capabilities.commerce.models import Organisation
from apps.capabilities.talent.models import BountyClaim

from .view_mixins import (
    ProductVisibilityCheckMixin,
    ProductManagementRequiredMixin,
    ProductSuccessUrlMixin,
    ProductServiceMixin,
    ProductContextMixin
)

logger = logging.getLogger(__name__)

class BaseProductView(ProductVisibilityCheckMixin, DetailView):
    """
    Base view for product-related views.
    Handles visibility checks and optional authentication.
    """
    model = Product
    slug_url_kwarg = 'product_slug'

class BaseAuthenticatedProductView(LoginRequiredMixin, ProductVisibilityCheckMixin, DetailView):
    """
    Base view for product-related views that always require authentication.
    """
    model = Product
    slug_url_kwarg = 'product_slug'
    login_url = reverse_lazy('security:sign_in')
    redirect_field_name = 'next'

class BaseManagementProductView(ProductManagementRequiredMixin, ProductContextMixin, DetailView):
    """
    Base view for product management operations.
    Always requires authentication and management permissions.
    """
    model = Product
    slug_url_kwarg = 'product_slug'
    login_url = reverse_lazy('security:sign_in')
    redirect_field_name = 'next'

class ProductDetailView(BaseProductView):
    """Public product details view - allows anonymous access for GLOBAL products"""
    template_name = "product_management/product/detail.html"
    context_object_name = 'product'

class CreateProductView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'product_management/create_product.html'
    
    def form_valid(self, form):
        success, error_message, product = ProductManagementService.create_product(
            self.request.user.person,
            form.cleaned_data
        )
        if success:
            return HttpResponseRedirect(reverse('product_management:product-summary', 
                                             kwargs={'product_slug': product.slug}))
        form.add_error(None, error_message)
        return self.form_invalid(form)

class UpdateProductView(BaseManagementProductView, UpdateView):
    """Update product view - requires management permissions"""
    form_class = ProductForm
    template_name = 'product_management/forms/product_form.html'
    
    def form_valid(self, form):
        success, error_msg = ProductManagementService.update_product(
            self.object,
            **form.cleaned_data
        )
        if success:
            return redirect('product_management:product-detail', slug=self.object.slug)
        messages.error(self.request, error_msg)
        return self.form_invalid(form)

    def get_success_url(self):
        return reverse("update-product", args=(self.object.id,))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        initial = {}
        
        if self.object.is_owned_by_person():
            initial["make_me_owner"] = (self.object.person == self.request.user.person)
            context["make_me_owner"] = initial["make_me_owner"]

        if self.object.is_owned_by_organisation():
            initial["organisation"] = self.object.organisation
            context["organisation"] = self.object.organisation

        context["form"] = self.form_class(instance=self.object, initial=initial)
        context["product_instance"] = self.object
        return context

class CreateContributorAgreementTemplateView(BaseManagementProductView):
    model = ProductContributorAgreementTemplate
    form_class = ContributorAgreementTemplateForm
    template_name = 'product_management/forms/product_form.html'

class ContributorAgreementTemplateView(BaseProductView, DetailView):
    """View for viewing contributor agreement templates"""
    model = ProductContributorAgreementTemplate
    template_name = "product_management/contributor_agreement_template_detail.html"
    context_object_name = 'template'

class CreateOrganisationView(BaseAuthenticatedProductView, CreateView):
    """View for creating organizations"""
    model = Organisation
    form_class = OrganisationForm
    template_name = "product_management/create_organisation.html"

class ProductAreaCreateView(BaseManagementProductView):
    """View for creating product areas"""
    model = ProductArea
    form_class = ProductAreaForm
    template_name = "product_management/product_area_create.html"

    def get_success_url(self):
        return reverse('product-tree', kwargs={'product_slug': self.kwargs['product_slug']})

class ProductAreaUpdateView(BaseManagementProductView):
    """View for updating product areas"""
    model = ProductArea
    form_class = ProductAreaForm
    template_name = "product_management/product_area_update.html"

    def get_success_url(self):
        return reverse('product-tree', kwargs={'product_slug': self.kwargs['product_slug']})

class ProductAreaDetailView(BaseProductView, DetailView):
    """View for product area details"""
    model = ProductArea
    template_name = "product_management/product_area_detail.html"
    context_object_name = 'product_area'

class CreateInitiativeView(BaseManagementProductView):
    """View for creating new initiatives"""
    model = Initiative
    form_class = InitiativeForm
    template_name = "product_management/create_initiative.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['product'] = get_object_or_404(Product, slug=self.kwargs['product_slug'])
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user.person
        form.instance.product = get_object_or_404(Product, slug=self.kwargs['product_slug'])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('product_management:initiative-detail', kwargs={
            'product_slug': self.kwargs['product_slug'],
            'pk': self.object.pk
        })

class InitiativeDetailView(BaseProductView, DetailView):
    """View for initiative details with management options"""
    model = Initiative
    template_name = "product_management/initiative_detail.html"
    context_object_name = 'initiative'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = get_object_or_404(Product, slug=self.kwargs['product_slug'])
        context['can_manage'] = RoleService.has_product_management_access(
            self.request.user.person, 
            context['product']
        )
        return context

class CreateBountyView(BaseManagementProductView, ProductSuccessUrlMixin, CreateView):
    """Create bounty view - requires management permissions"""
    model = Bounty
    form_class = BountyForm
    template_name = "product_management/create_bounty.html"
    success_url_name = 'bounty-detail'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['product'] = self.get_product()
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user.person
        form.instance.challenge = get_object_or_404(
            Challenge, 
            pk=self.kwargs['challenge_id'],
            product=self.get_product()
        )
        return super().form_valid(form)

class UpdateBountyView(BaseManagementProductView):
    """View for updating bounties"""
    model = Bounty
    form_class = BountyForm
    template_name = "product_management/update_bounty.html"

    def get_success_url(self):
        return reverse('product_management:bounty-detail',
                      kwargs={'product_slug': self.object.challenge.product.slug,
                             'challenge_id': self.object.challenge.id,
                             'pk': self.object.id})

class DeleteBountyView(BaseManagementProductView):
    """View for deleting bounties"""
    model = Bounty
    template_name = "product_management/delete_bounty.html"
    
    def get_success_url(self):
        return reverse('product_management:product-bounties', 
                      kwargs={'product_slug': self.kwargs['product_slug']})

class BountyClaimView(BaseProductView, DetailView):
    """View for bounty claims"""
    model = BountyClaim
    template_name = "product_management/bounty_claim.html"
    context_object_name = 'claim'

class DeleteBountyClaimView(BaseProductView, DeleteView):
    """View for deleting bounty claims"""
    model = BountyClaim
    template_name = "product_management/delete_bounty_claim.html"

    def get_success_url(self):
        return reverse('product_management:bounty-detail', 
                      kwargs={'product_slug': self.object.bounty.challenge.product.slug,
                             'challenge_id': self.object.bounty.challenge.id,
                             'pk': self.object.bounty.id})

class UpdateChallengeView(BaseManagementProductView):
    """View for updating challenges"""
    model = Challenge
    form_class = ChallengeForm
    template_name = "product_management/update_challenge.html"

    def get_success_url(self):
        return reverse('product_management:challenge-detail', 
                      kwargs={'product_slug': self.kwargs['product_slug'], 
                             'pk': self.object.pk})

class DeleteChallengeView(BaseManagementProductView):
    """View for deleting challenges"""
    model = Challenge
    template_name = "product_management/delete_challenge.html"

    def get_success_url(self):
        return reverse('product_management:product-challenges', 
                      kwargs={'product_slug': self.kwargs['product_slug']})

class CreateProductIdea(BaseProductView, CreateView):
    """View for creating new product ideas."""
    template_name = "product_management/add_product_idea.html"
    form_class = IdeaForm

    def post(self, request, *args, **kwargs):
        form = IdeaForm(request.POST)
        if form.is_valid():
            product = get_object_or_404(Product, slug=kwargs.get("product_slug"))
            success, error, idea = IdeaService.create_idea(
                form.cleaned_data,
                self.request.user.person,
                product
            )
            if success:
                return redirect("product_management:product-ideas-bugs", **kwargs)
            messages.error(self.request, error)
        return super().post(request, *args, **kwargs)


class UpdateProductIdea(BaseProductView, UpdateView):
    """View for updating existing product ideas."""
    template_name = "product_management/update_product_idea.html"
    model = Idea
    form_class = IdeaForm

    def dispatch(self, request, *args, **kwargs):
        idea = get_object_or_404(Idea, pk=kwargs['pk'])
        if not IdeaService.can_modify_idea(idea, request.user.person):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        idea = self.get_object()
        if not IdeaService.can_modify_idea(idea, self.request.user.person):
            raise PermissionDenied

        form = IdeaForm(request.POST, instance=idea)
        if form.is_valid():
            success, error = IdeaService.update_idea(idea, form.cleaned_data)
            if success:
                return redirect("product_idea_detail", **kwargs)
            messages.error(self.request, error)
        return super().post(request, *args, **kwargs)


class CreateProductBug(BaseProductView, CreateView):
    """View for creating new product bugs."""
    template_name = "product_management/add_product_bug.html"
    form_class = BugForm

    def post(self, request, *args, **kwargs):
        form = BugForm(request.POST)

        if form.is_valid():
            person = self.request.user.person
            product = get_object_or_404(Product, slug=kwargs.get("product_slug"))

            bug = form.save(commit=False)
            bug.person = person
            bug.product = product
            bug.save()

            return redirect("product_management:product-ideas-bugs", **kwargs)

        return super().post(request, *args, **kwargs)


class UpdateProductBug(BaseProductView, UpdateView):
    """View for updating existing product bugs."""
    template_name = "product_management/update_product_bug.html"
    model = Bug
    form_class = BugForm

    def get(self, request, *args, **kwargs):
        bug = self.get_object()
        if bug.person != self.request.user.person:
            raise PermissionDenied
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        bug = self.get_object()
        if bug.person != self.request.user.person:
            raise PermissionDenied

        form = BugForm(request.POST, instance=bug)
        if form.is_valid():
            form.save()
            return redirect("product_bug_detail", **kwargs)

        return super().post(request, *args, **kwargs)


class VoteView(LoginRequiredMixin, View):
    login_url = reverse_lazy('security:sign_in')
    redirect_field_name = None

    def post(self, request, *args, **kwargs):
        idea = get_object_or_404(Idea, pk=kwargs['pk'])
        if not ProductService.has_product_visibility_access(request.user.person, idea.product):
            raise PermissionDenied
        # ... rest of the view logic ...

@login_required
def cast_vote_for_idea(request, pk):
    """
    Toggle a vote for an idea
    """
    idea = get_object_or_404(Idea, pk=pk)
    
    # Check if user has access to view the product
    if not ProductService.has_product_visibility_access(request.user, idea.product):
        raise PermissionDenied
        
    success, error, vote_count = IdeaService.toggle_vote(idea, request.user)
    
    if not success:
        return JsonResponse({'error': error}, status=400)
        
    return JsonResponse({'vote_count': vote_count})

class UpdateIdeaView(LoginRequiredMixin, UpdateView):
    model = Idea
    form_class = IdeaForm
    template_name = 'product_management/forms/idea_form.html'
    login_url = reverse_lazy('security:sign_in')
    redirect_field_name = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(self.login_url)
            
        self.object = self.get_object()
        if not IdeaService.can_modify_idea(request.user.person, self.object):
            raise PermissionDenied
            
        return super().dispatch(request, *args, **kwargs)

class CreateIdeaView(LoginRequiredMixin, CreateView):
    model = Idea
    template_name = 'product_management/create_idea.html'
    fields = ['title', 'description']  # Add required fields
    
    def form_valid(self, form):
        success, error_message, idea = IdeaService.create_idea(
            self.request.user.person,
            self.kwargs['product_slug'],
            form.cleaned_data
        )
        if success:
            return HttpResponseRedirect(reverse('product_management:idea-detail', 
                                             kwargs={'product_slug': self.kwargs['product_slug'],
                                                   'idea_id': idea.id}))
        form.add_error(None, error_message)
        return self.form_invalid(form)

