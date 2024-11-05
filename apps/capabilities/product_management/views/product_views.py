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

logger = logging.getLogger(__name__)

class BaseProductView(LoginRequiredMixin):
    """Base class for product views with common functionality"""
    
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
    login_url = "sign_in"

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

class ProductChallengesView(LoginRequiredMixin, TemplateView):
    template_name = 'product_management/product_challenges.html'
    
    STATUS_COLORS = {
        'Draft': 'text-gray-500 border-gray-500',
        'Blocked': 'text-red-700 border-red-700',
        'Active': 'text-green-700 border-green-700',
        'Completed': 'text-blue-700 border-blue-700',
        'Cancelled': 'text-gray-400 border-gray-400',
    }
    
    def get_queryset(self, product):
        return Challenge.objects.filter(
            product=product
        ).select_related(
            'product_area',
            'created_by'
        ).prefetch_related(
            'bounty_set'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get product from URL using slug instead of ID
        product_slug = self.kwargs.get('product_slug')
        product = get_object_or_404(Product, slug=product_slug)
        
        challenges = self.get_queryset(product)
        
        # Process each challenge
        for challenge in challenges:
            challenge.status_color = self.STATUS_COLORS.get(challenge.status, '')
            challenge.bounty_points = challenge.get_bounty_points()
            challenge.has_bounty = challenge.has_bounty()
        
        context.update({
            'challenges': challenges,
            'product': product,
            'status_choices': Challenge.ChallengeStatus.choices,
            'priority_choices': Challenge.ChallengePriority.choices,
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


class ProductListView(BaseProductView, ListView):
    """View for listing all products"""
    model = Product
    template_name = "product_management/products.html"
    context_object_name = 'products'

    def get_queryset(self):
        return Product.objects.all().order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_create'] = True  # Or add logic to determine if user can create products
        return context

class ProductRedirectView(BaseProductView, RedirectView):
    """Redirects to the product summary view"""
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        product_slug = kwargs.get('product_slug')
        return reverse('product_management:product-summary', kwargs={'product_slug': product_slug})

class ProductSummaryView(BaseProductView, TemplateView):
    """View for displaying product summary"""
    template_name = "product_management/product_summary.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = get_object_or_404(Product, slug=self.kwargs['product_slug'])
        
        # Add product to context
        context['product'] = product
        
        # Get active challenges
        challenges = Challenge.objects.filter(
            product=product, 
            status=Challenge.ChallengeStatus.ACTIVE
        )
        
        # Check product management access
        can_modify_product = RoleService.has_product_management_access(
            self.request.user.person, 
            product
        )

        # Get product tree data
        product_tree = product.product_trees.first()
        if product_tree:
            product_areas = ProductArea.get_root_nodes().filter(product_tree=product_tree)
            tree_data = [utils.serialize_tree(node) for node in product_areas]
        else:
            tree_data = []

        context.update({
            'challenges': challenges,
            'can_modify_product': can_modify_product,
            'tree_data': tree_data,
        })

        # Add URL segment data
        url_segments = self.request.path.strip('/').split('/')
        context['url_segment'] = url_segments
        context['last_segment'] = url_segments[-1] if url_segments else ''

        return context

class ProductInitiativesView(BaseProductView, TemplateView):
    """View for displaying product initiatives"""
    template_name = "product_management/product_initiatives.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = get_object_or_404(Product, slug=self.kwargs['product_slug'])
        
        initiatives = Initiative.objects.filter(product=product).order_by('-created_at')
        
        context.update({
            'product': product,
            'initiatives': initiatives,
            'can_manage': RoleService.has_product_management_access(
                self.request.user.person, 
                product
            )
        })
        return context

class BountyListView(BaseProductView, ListView):
    """View for listing all bounties"""
    model = Bounty
    template_name = "product_management/bounty/list.html"
    context_object_name = 'bounties'
    paginate_by = 20  # Show 20 bounties per page

    def get_queryset(self):
        return (Bounty.objects
                .select_related('challenge', 'challenge__product')  # Fetch related fields in single query
                .only(
                    'id', 'title', 'points', 'status', 'created_at',
                    'challenge__title', 'challenge__product__name'
                )  # Select only needed fields
                .order_by('-created_at'))

class ProductBountyListView(BaseProductView, ListView):
    """View for listing product-specific bounties"""
    model = Bounty
    template_name = "product_management/product_bounties.html"
    context_object_name = 'bounties'

    def get_queryset(self):
        product = get_object_or_404(Product, slug=self.kwargs['product_slug'])
        return Bounty.objects.filter(challenge__product=product).order_by('-created_at')

class ProductTreeInteractiveView(BaseProductView, TemplateView):
    """View for interactive product tree"""
    template_name = "product_management/product_tree_interactive.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = get_object_or_404(Product, slug=self.kwargs['product_slug'])
        
        product_tree = product.product_trees.first()
        if product_tree:
            product_areas = ProductArea.get_root_nodes().filter(product_tree=product_tree)
            tree_data = [utils.serialize_tree(node) for node in product_areas]
        else:
            tree_data = []
            
        context.update({
            'product': product,
            'tree_data': tree_data,
            'can_manage': RoleService.has_product_management_access(
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

class ProductAreaDetailView(BaseProductView, DetailView):
    """View for product area details"""
    model = ProductArea
    template_name = "product_management/product_area_detail.html"
    context_object_name = 'product_area'

class ProductPeopleView(BaseProductView, TemplateView):
    """View for managing product role assignments"""
    template_name = "product_management/product_people.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = get_object_or_404(Product, slug=self.kwargs['product_slug'])
        
        # Get product people and sort by role
        product_people = ProductRoleAssignment.objects.filter(product=product).order_by('role')
        
        # Group by role and convert to dict
        grouped_people = {}
        for role, group in groupby(product_people, key=attrgetter('role')):
            grouped_people[role] = list(group)
        
        # Sort roles in reverse order
        sorted_groups = dict(sorted(grouped_people.items(), reverse=True))
        
        context.update({
            'product': product,
            'grouped_product_people': sorted_groups.items(),
        })
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

class BountyDetailView(BaseProductView, DetailView):
    """View for bounty details"""
    model = Bounty
    template_name = "product_management/bounty_detail.html"
    context_object_name = 'bounty'

class BountyClaimView(BaseProductView, DetailView):
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

class ChallengeDetailView(BaseProductView, DetailView):
    """View for challenge details"""
    model = Challenge
    template_name = "product_management/challenge_detail.html"
    context_object_name = 'challenge'

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

class ProductBountyListView(View):
    def get(self, request, product_slug):
        # Get the last segment of the URL path
        last_segment = request.path.strip('/').split('/')[-1]
        
        context = {
            'product_slug': product_slug,
            'last_segment': last_segment,
            'bounties': [],  # Your bounties queryset
        }
        return render(request, 'product_management/product_detail_base.html', context)
