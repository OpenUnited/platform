import uuid
from typing import Any, Dict
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import BadRequest
from django.db import models
from django.forms import ValidationError
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    RedirectView,
    TemplateView,
    UpdateView,
    View
)

from apps.canopy import utils as canopy_utils
from apps.capabilities.commerce.models import Organisation
from apps.capabilities.product_management.views.view_mixins import ProductVisibilityCheckMixin
from apps.common import mixins as common_mixins
from .. import utils
from ..forms import (
    BountyForm,
    ContributorAgreementTemplateForm,
    OrganisationForm,
    ChallengeForm,
    ProductAreaForm,
    ProductForm,
    InitiativeForm
)
from apps.capabilities.security.models import ProductRoleAssignment
from apps.capabilities.security.services import RoleService
from apps.capabilities.talent.forms import PersonSkillFormSet
from apps.capabilities.talent.models import BountyClaim, Expertise, Skill
from apps.capabilities.talent.utils import serialize_skills
from apps.utility.utils import serialize_other_type_tree
from apps.capabilities.product_management.models import (
    Bounty,
    Challenge,
    Initiative,
    Product,
    ProductArea,
    ProductContributorAgreement,
    ProductContributorAgreementTemplate,
)
from ..utils import require_product_management_access
from itertools import groupby
from operator import attrgetter
from django.db.models import Count

from apps.capabilities.product_management.services import ProductService

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

class BasePublicProductView:
    """Base class for public product views"""
    pass

class CreateProductView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'product_management/create_product.html'
    success_url = reverse_lazy('portal:dashboard')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['person'] = self.request.user.person
        return kwargs

class UpdateProductView(BaseProductView, common_mixins.AttachmentMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "product_management/update_product.html"
    login_url = 'security:sign_in'

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
        return super().form_save(form)

class ProductDetailView(BaseProductView, DetailView):
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

class ProductChallengesView(ProductVisibilityCheckMixin, DetailView):
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
        """Get challenges for the current product with optimized queries"""
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
        product = self.object
        current_person = self.request.user.person if self.request.user.is_authenticated else None
        
        context.update({
            'challenges': self.get_challenges_queryset(),
            'status_colors': self.STATUS_COLORS,
            'show_actions': current_person and RoleService.has_product_access(current_person, product),
            'can_modify': current_person and RoleService.has_product_management_access(current_person, product),
        })
        return context

class CreateContributorAgreementTemplateView(BaseProductView, common_mixins.AttachmentMixin, 
                                           common_mixins.HTMXInlineFormValidationMixin, CreateView):
    model = ProductContributorAgreementTemplate
    form_class = ContributorAgreementTemplateForm
    template_name = "product_management/create_contributor_agreement_template.html"
    login_url = "sign_in"

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        if product_slug := self.kwargs.get("product_slug", None):
            kwargs.update(initial={"product": Product.objects.get(slug=product_slug)})
        return kwargs

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.created_by = request.user.person
            instance.save()
            messages.success(request, "The contribution agreement is successfully created!")
            self.success_url = reverse(
                "contributor-agreement-template-detail",
                args=(instance.product.slug, instance.id,),
            )
            return redirect(self.success_url)
        return super().post(request, *args, **kwargs)


class ProductListView(ListView):
    """View for listing all products"""
    model = Product
    template_name = "product_management/products.html"
    context_object_name = 'products'
    paginate_by = 12  # Optional: Add pagination if needed

    def get_queryset(self):
        return ProductService.get_visible_products(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_create'] = self.request.user.is_authenticated
        return context

class ProductRedirectView(BasePublicProductView, ProductVisibilityCheckMixin, RedirectView):
    permanent = False

    def get_product(self):
        # Override get_product to get product directly from slug
        return get_object_or_404(Product, slug=self.kwargs['product_slug'])

    def get_redirect_url(self, *args, **kwargs):
        product_slug = kwargs.get('product_slug')
        return reverse('product_management:product-summary', kwargs={'product_slug': product_slug})

class ProductSummaryView(BasePublicProductView, ProductVisibilityCheckMixin, DetailView):
    model = Product
    template_name = "product_management/product_summary.html"
    slug_url_kwarg = 'product_slug'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product_slug'] = self.kwargs['product_slug']
        context['challenges'] = Challenge.objects.filter(product=self.object)
        return context

class ProductInitiativesView(BasePublicProductView, ProductVisibilityCheckMixin, ListView):
    """View for product initiatives"""
    model = Initiative
    template_name = "product_management/product_initiatives.html"
    context_object_name = 'initiatives'

    def get_object(self):
        """Required by ProductVisibilityCheckMixin"""
        return get_object_or_404(Product, slug=self.kwargs['product_slug'])

    def get_queryset(self):
        self.product = self.get_object()
        return Initiative.objects.filter(
            product=self.product
        ).select_related('product')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.product
        context['product_slug'] = self.kwargs['product_slug']
        context['last_segment'] = self.request.path.strip('/').split('/')[-1]
        if self.request.user.is_authenticated:
            context['can_manage'] = RoleService.has_product_management_access(
                self.request.user.person, 
                self.product
            )
        return context

class BountyListView(ListView):
    """View for listing all bounties"""
    model = Bounty
    template_name = "product_management/bounty/list.html"
    context_object_name = 'bounties'
    paginate_by = 20

    def get_queryset(self):
        # If product_slug is in kwargs, filter by that product
        if 'product_slug' in self.kwargs:
            product = get_object_or_404(Product, slug=self.kwargs['product_slug'])
            return (Bounty.objects
                    .filter(challenge__product=product)
                    .select_related('challenge', 'challenge__product')
                    .order_by('-created_at'))
        else:
            # Otherwise, show all visible bounties
            return (Bounty.objects
                    .filter(
                        challenge__product__in=ProductService.get_visible_products(self.request.user)
                    )
                    .select_related('challenge', 'challenge__product')
                    .order_by('-created_at'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'product_slug' in self.kwargs:
            product = get_object_or_404(Product, slug=self.kwargs['product_slug'])
            context['product'] = product
            if self.request.user.is_authenticated:
                context['can_manage'] = RoleService.has_product_management_access(
                    self.request.user.person,
                    product
                )
        return context

class ProductBountiesView(ProductVisibilityCheckMixin, ListView):
    """View for listing product-specific bounties"""
    model = Bounty
    template_name = "product_management/product_bounties.html"
    context_object_name = 'bounties'
    paginate_by = 20

    def get_product(self):
        """Required by ProductVisibilityCheckMixin"""
        return get_object_or_404(Product, slug=self.kwargs['product_slug'])

    def get_queryset(self):
        product = self.get_product()
        return (Bounty.objects
                .filter(challenge__product=product)
                .select_related('challenge', 'challenge__product')
                .order_by('-created_at'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_product()
        context['product'] = product
        if self.request.user.is_authenticated:
            context['can_manage'] = RoleService.has_product_management_access(
                self.request.user.person,
                product
            )
        return context

class ProductTreeInteractiveView(ProductVisibilityCheckMixin, TemplateView):
    """View for interactive product tree"""
    template_name = "product_management/product_tree.html"

    def get_product(self):
        """Required by ProductVisibilityCheckMixin"""
        return get_object_or_404(Product, slug=self.kwargs['product_slug'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_product()
        
        product_tree = product.product_trees.first()
        if product_tree:
            product_areas = ProductArea.get_root_nodes().filter(product_tree=product_tree)
            tree_data = [utils.serialize_tree(node) for node in product_areas]
        else:
            tree_data = []
            
        context.update({
            'product': product,
            'tree_data': tree_data,
            'can_manage': self.request.user.is_authenticated and RoleService.has_product_management_access(
                self.request.user.person, 
                product
            )
        })
        return context

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

class ProductAreaDetailView(ProductVisibilityCheckMixin, DetailView):
    """View for product area details"""
    model = ProductArea
    template_name = "product_management/product_area_detail.html"
    context_object_name = 'product_area'

    def get_product(self):
        """Required by ProductVisibilityCheckMixin"""
        return self.get_object().product_tree.product

class ProductPeopleView(ListView):
    template_name = 'product_management/product_people.html'

    def get_queryset(self):
        self.product = get_object_or_404(Product, slug=self.kwargs['product_slug'])
        # Get all members using RoleService
        return RoleService.get_product_members(self.product)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.product
        
        # Get role assignments for all members
        product_roles = ProductRoleAssignment.objects.filter(
            product=self.product
        ).select_related('person').order_by('role')
        
        # Group by role for the template
        context['grouped_product_people'] = [
            (role, list(assignments)) 
            for role, assignments in groupby(product_roles, key=lambda x: x.role)
        ]
        
        return context


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
    """View for initiative details"""
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

def redirect_challenge_to_bounties(request):
    """Redirect legacy challenge URLs to the bounties view"""
    return redirect('product_management:bounties')

class DeleteBountyView(BaseProductView, DeleteView):
    """View for deleting bounties"""
    model = Bounty
    template_name = "product_management/delete_bounty.html"
    
    def get_success_url(self):
        return reverse('product_management:product-bounties', 
                      kwargs={'product_slug': self.kwargs['product_slug']})

class ContributorAgreementTemplateView(BaseProductView, DetailView):
    """View for viewing contributor agreement templates"""
    model = ProductContributorAgreementTemplate
    template_name = "product_management/contributor_agreement_template_detail.html"
    context_object_name = 'template'

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

class BountyDetailView(ProductVisibilityCheckMixin, DetailView):
    """View for bounty details"""
    model = Bounty
    template_name = "product_management/bounty_detail.html"
    context_object_name = 'bounty'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        return obj

    def get_product(self):
        """Required by ProductVisibilityCheckMixin"""
        return self.get_object().challenge.product

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bounty = self.object
        product = bounty.challenge.product

        # Default values for anonymous users
        context['data'] = {
            'product': product,
            'challenge': bounty.challenge,
            'bounty': bounty,
            'show_actions': False,
            'can_be_modified': False,
            'created_bounty_claim_request': False
        }

        # Add authenticated user specific context
        if self.request.user.is_authenticated:
            current_person = self.request.user.person
            context['data'].update({
                'show_actions': RoleService.has_product_access(current_person, product),
                'can_be_modified': RoleService.has_product_management_access(current_person, product),
                'created_bounty_claim_request': BountyClaim.objects.filter(
                    bounty=bounty,
                    person=current_person
                ).exists()
            })
        
        context['expertise_list'] = bounty.expertise.all()
        return context

class BountyClaimView(DetailView):
    """View for bounty claims"""
    model = BountyClaim
    template_name = "product_management/bounty_claim.html"
    context_object_name = 'claim'

class CreateOrganisationView(BaseProductView, CreateView):
    """View for creating organizations"""
    model = Organisation
    form_class = OrganisationForm
    template_name = "product_management/create_organisation.html"
    success_url = reverse_lazy('product_management:products')

class ChallengeDetailView(ProductVisibilityCheckMixin, DetailView):
    model = Challenge
    template_name = 'product_management/challenge_detail.html'
    context_object_name = 'challenge'

    def get_object(self, queryset=None):
        """Get the challenge object and ensure proper field selection"""
        if queryset is None:
            queryset = self.get_queryset()
            
        # Filter by both the product slug and challenge ID
        queryset = queryset.filter(
            product__slug=self.kwargs['product_slug'],
            pk=self.kwargs['pk']
        ).select_related(
            'product',
            'initiative',
            'product_area',
            'created_by'
        )
        
        obj = queryset.get()
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.object.product
        if self.request.user.is_authenticated:
            context['can_manage'] = RoleService.has_product_management_access(
                self.request.user.person,
                self.object.product
            )
        return context

class DeleteBountyClaimView(BaseProductView, DeleteView):
    """View for deleting bounty claims"""
    model = BountyClaim
    template_name = "product_management/delete_bounty_claim.html"

    def get_success_url(self):
        return reverse('product_management:bounty-detail', 
                      kwargs={'product_slug': self.object.bounty.challenge.product.slug,
                             'challenge_id': self.object.bounty.challenge.id,
                             'pk': self.object.bounty.id})

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

class ProductContributorsView(ListView):
    template_name = 'product_management/product_people.html'
    context_object_name = 'contributors'

    def get_queryset(self):
        self.product = get_object_or_404(Product, slug=self.kwargs['product_slug'])
        return RoleService.get_product_members(self.product)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.product
        
        # Optionally add role information for each contributor
        contributors_with_roles = []
        for person in context['contributors']:
            roles = ProductRoleAssignment.objects.filter(
                person=person,
                product=self.product
            ).values_list('role', flat=True)
            contributors_with_roles.append({
                'person': person,
                'roles': list(roles)
            })
        context['contributors_with_roles'] = contributors_with_roles
        
        return context
