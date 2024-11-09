"""
Product Management views for public and unauthenticated access.

Note: For authenticated management interfaces, see the portal app (apps/portal/).
The portal app provides protected views and richer management interfaces for these
same product services, while these views handle public-facing functionality.

Views in this module focus on:
- Public product pages
- Unauthenticated access
- Basic product interactions

For full management capabilities, see portal.views.
"""

import logging
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    UpdateView,
    View
)
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect

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

logger = logging.getLogger(__name__)

class BaseProductView(LoginRequiredMixin):
    """Base class for product management views requiring authentication"""
    login_url = 'security:sign_in'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
            
        # Only check product access if product_slug is in kwargs
        if 'product_slug' in kwargs:
            try:
                product = Product.objects.get(slug=kwargs['product_slug'])
                if not RoleService.has_product_management_access(request.user.person, product):
                    messages.error(request, "You do not have access to manage this product")
                    return redirect('product_management:products')
            except Product.DoesNotExist:
                messages.error(request, "Product not found")
                return redirect('product_management:products')
                
        return super().dispatch(request, *args, **kwargs)

class CreateProductView(LoginRequiredMixin, CreateView):
    """View for creating new products"""
    model = Product
    form_class = ProductForm
    template_name = 'product_management/create_product.html'
    success_url = reverse_lazy('portal:dashboard')

    def form_valid(self, form):
        success, error, product = ProductManagementService.create_product(
            form.cleaned_data,
            self.request.user.person
        )
        if not success:
            messages.error(self.request, error)
            return self.form_invalid(form)
        self.object = product
        return super().form_valid(form)

class UpdateProductView(BaseProductView, common_mixins.AttachmentMixin, UpdateView):
    """View for updating existing products"""
    model = Product
    form_class = ProductForm
    template_name = "product_management/update_product.html"

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

    def form_valid(self, form):
        success, error = ProductManagementService.update_product(
            self.object,
            form.cleaned_data
        )
        if not success:
            messages.error(self.request, error)
            return self.form_invalid(form)
        return super().form_valid(form)

class ProductDetailView(BaseProductView, DetailView):
    """View for product details with management actions"""
    template_name = "product_management/product/detail.html"
    model = Product
    context_object_name = 'product'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        context["product_photo_url"] = product.get_photo_url()
        context["can_manage"] = RoleService.has_product_management_access(
            self.request.user.person, 
            product
        )
        return context

class CreateContributorAgreementTemplateView(BaseProductView, common_mixins.AttachmentMixin, 
                                           common_mixins.HTMXInlineFormValidationMixin, CreateView):
    """View for creating contributor agreement templates"""
    model = ProductContributorAgreementTemplate
    form_class = ContributorAgreementTemplateForm
    template_name = "product_management/create_contributor_agreement_template.html"

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        if product_slug := self.kwargs.get("product_slug", None):
            kwargs.update(initial={"product": Product.objects.get(slug=product_slug)})
        return kwargs

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            success, error, template = ContributorAgreementService.create_template(
                form.cleaned_data,
                request.user.person
            )
            if not success:
                messages.error(request, error)
                return self.form_invalid(form)
                
            messages.success(request, "The contribution agreement is successfully created!")
            self.success_url = reverse(
                "contributor-agreement-template-detail",
                args=(template.product.slug, template.id,),
            )
            return redirect(self.success_url)
        return super().post(request, *args, **kwargs)

class ContributorAgreementTemplateView(BaseProductView, DetailView):
    """View for viewing contributor agreement templates"""
    model = ProductContributorAgreementTemplate
    template_name = "product_management/contributor_agreement_template_detail.html"
    context_object_name = 'template'

class CreateOrganisationView(BaseProductView, CreateView):
    """View for creating organizations"""
    model = Organisation
    form_class = OrganisationForm
    template_name = "product_management/create_organisation.html"
    success_url = reverse_lazy('product_management:products')

class ProductAreaCreateView(BaseProductView, CreateView):
    """View for creating product areas"""
    model = ProductArea
    form_class = ProductAreaForm
    template_name = "product_management/product_area_create.html"

    def get_success_url(self):
        return reverse('product-tree', kwargs={'product_slug': self.kwargs['product_slug']})

class ProductAreaUpdateView(BaseProductView, UpdateView):
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

class CreateInitiativeView(BaseProductView, CreateView):
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

class BountyDetailView(BaseProductView, DetailView):
    """View for bounty details with management options"""
    model = Bounty
    template_name = "product_management/bounty_detail.html"
    context_object_name = 'bounty'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bounty = self.object
        product = bounty.challenge.product

        context['data'] = {
            'product': product,
            'challenge': bounty.challenge,
            'bounty': bounty,
            'show_actions': True,  # Always true for management view
            'can_be_modified': RoleService.has_product_management_access(
                self.request.user.person,
                product
            )
        }
        
        context['expertise_list'] = bounty.expertise.all()
        return context

class CreateBountyView(BaseProductView, CreateView):
    """View for creating bounties"""
    model = Bounty
    form_class = BountyForm
    template_name = "product_management/create_bounty.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['product'] = get_object_or_404(Product, slug=self.kwargs['product_slug'])
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user.person
        form.instance.challenge = get_object_or_404(
            Challenge, 
            pk=self.kwargs['challenge_id'],
            product__slug=self.kwargs['product_slug']
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('product_management:bounty-detail', kwargs={
            'product_slug': self.kwargs['product_slug'],
            'challenge_id': self.kwargs['challenge_id'],
            'pk': self.object.pk
        })

class UpdateBountyView(BaseProductView, UpdateView):
    """View for updating bounties"""
    model = Bounty
    form_class = BountyForm
    template_name = "product_management/update_bounty.html"

    def get_success_url(self):
        return reverse('product_management:bounty-detail',
                      kwargs={'product_slug': self.object.challenge.product.slug,
                             'challenge_id': self.object.challenge.id,
                             'pk': self.object.id})

class DeleteBountyView(BaseProductView, DeleteView):
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

class UpdateChallengeView(BaseProductView, UpdateView):
    """View for updating challenges"""
    model = Challenge
    form_class = ChallengeForm
    template_name = "product_management/update_challenge.html"

    def get_success_url(self):
        return reverse('product_management:challenge-detail', 
                      kwargs={'product_slug': self.kwargs['product_slug'], 
                             'pk': self.object.pk})

class DeleteChallengeView(BaseProductView, DeleteView):
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
                return redirect("product_ideas_bugs", **kwargs)
            messages.error(self.request, error)
        return super().post(request, *args, **kwargs)


class UpdateProductIdea(BaseProductView, UpdateView):
    """View for updating existing product ideas."""
    template_name = "product_management/update_product_idea.html"
    model = Idea
    form_class = IdeaForm

    def get(self, request, *args, **kwargs):
        idea = self.get_object()
        if not IdeaService.can_modify_idea(idea, self.request.user.person):
            raise PermissionDenied
        return super().get(request, *args, **kwargs)

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

            return redirect("product_ideas_bugs", **kwargs)

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


class CastVoteView(LoginRequiredMixin, View):
    """
    View for handling idea voting functionality
    """
    def post(self, request, pk):
        idea = get_object_or_404(Idea, pk=pk)
        
        # Check if user has visibility access to the product
        if not ProductService.has_product_visibility_access(idea.product, request.user):
            raise PermissionDenied
            
        success, error_message, vote_count = IdeaService.toggle_vote(idea, request.user)
        
        if not success:
            return JsonResponse({'error': error_message}, status=400)
            
        return JsonResponse({
            'success': True,
            'voteCount': vote_count
        })

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

