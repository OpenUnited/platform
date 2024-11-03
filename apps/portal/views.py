"""
Views for the product management portal.

This module handles the presentation layer for product management portal features,
including the portal overview, work review, bounty management, and contributor agreements.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, TemplateView, DeleteView, UpdateView, View, DetailView, CreateView
from django.shortcuts import get_object_or_404, render, redirect
from django.db import models
from django.urls import reverse, reverse_lazy
from django.db.models import Count, Q
from django.core.exceptions import PermissionDenied, BadRequest
from django.contrib import messages
from django.http import HttpResponseBadRequest
from django.views.generic.edit import UpdateView

from apps.capabilities.product_management.models import (
    Product,
    ProductContributorAgreementTemplate,
    Bounty,
    Challenge,
    FileAttachment
)
from apps.capabilities.security.models import ProductRoleAssignment
from apps.capabilities.talent.models import BountyClaim, BountyDeliveryAttempt
from apps.capabilities.security.services import RoleService
from apps.portal.forms import PortalProductForm, PortalProductRoleAssignmentForm, ProductSettingsForm
from apps.common import mixins as common_mixins
from apps.common.mixins import AttachmentMixin
from apps.capabilities.product_management.forms import ProductForm


class PortalBaseView(LoginRequiredMixin, TemplateView):
    """Base view for portal pages with common functionality."""
    login_url = "sign_in"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if not hasattr(user, 'person'):
            return context
            
        person = user.person
        # Get all products user has access to
        user_products = RoleService.get_user_products(person=person)
        # Get products where user has management rights
        managed_products = RoleService.get_managed_products(person=person)
        
        context.update({
            "products": user_products,  # Add this for all accessible products
            "managed_products": managed_products,
            "person": person,
        })
        return context

def bounty_claim_actions(request, pk):
    instance = BountyClaim.objects.get(pk=pk)
    action_type = request.GET.get("action")
    if action_type == "accept":
        instance.status = BountyClaim.Status.GRANTED

        # If one claim is accepted for a particular challenge, the other claims automatically fails.
        challenge = instance.bounty.challenge
        _ = BountyClaim.objects.filter(bounty__challenge=challenge).update(status=BountyClaim.Status.REJECTED)
    elif action_type == "reject":
        instance.status = BountyClaim.Status.REJECTED
    else:
        raise BadRequest()

    instance.save()

    return redirect(reverse("portal:product-bounties", args=(instance.bounty.challenge.product.slug,)))


class PortalProductSettingView(LoginRequiredMixin, AttachmentMixin, DetailView):
    template_name = "product_settings.html"
    model = Product
    slug_url_kwarg = 'product_slug'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = ProductForm(instance=self.object)
        context.update({
            'form': form,
            'detail_url': self.object.get_absolute_url(),
        })
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = PortalProductForm(request.POST, request.FILES, instance=self.object)
        attachment_formset = self.get_attachment_formset()

        if form.is_valid() and attachment_formset.is_valid():
            form.save()
            attachment_formset.save()
            return redirect(self.object.get_absolute_url())

        context = {
            'form': form,
            'product': self.object,
            'attachment_formset': attachment_formset,
            'detail_url': self.object.get_absolute_url()
        }
        return render(request, self.template_name, context)


class PortalManageBountiesView(PortalBaseView, TemplateView):
    template_name = "my_bounties.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        person = self.request.user.person
        queryset = BountyClaim.objects.filter(
            person=person,
            status__in=[
                BountyClaim.Status.GRANTED,
                BountyClaim.Status.REQUESTED,
            ],
        )
        context.update({"bounty_claims": queryset})
        return context
    
class PortalUpdateProductUserView(PortalBaseView):
    model = ProductRoleAssignment
    form_class = PortalProductRoleAssignmentForm
    template_name = "update_product_user.html"
    login_url = "sign_in"
    context_object_name = "product_role_assignment"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context["search_result"]:
            return context

        slug = self.kwargs.get("product_slug")
        product = Product.objects.get(slug=slug)
        product_users = RoleService.get_product_members(product=product)

        context["product"] = product
        context["product_users"] = product_users

        return context

    def post(self, request, *args, **kwargs):
        product_role_assignment = ProductRoleAssignment.objects.get(pk=kwargs.get("pk"))
        product = Product.objects.get(slug=kwargs.get("product_slug"))

        form = PortalProductRoleAssignmentForm(request.POST, instance=product_role_assignment)

        if form.is_valid():
            person = form.cleaned_data['person']
            role = form.cleaned_data['role']
            
            RoleService.assign_product_role(
                person=person,
                product=product,
                role=role
            )

            self.success_url = reverse("portal:manage-users", args=(product.slug,))
            return redirect(self.success_url)

        return super().post(request, *args, **kwargs)

class PortalBountyClaimRequestsView(LoginRequiredMixin, ListView):
    model = BountyClaim
    context_object_name = "bounty_claims"
    template_name = "bounty_claim_requests.html"
    login_url = "sign_in"

    def get_queryset(self):
        person = self.request.user.person
        return BountyClaim.objects.filter(
            person=person,
            status__in=[BountyClaim.Status.GRANTED, BountyClaim.Status.REQUESTED],
        )

class PortalManageUsersView(PortalBaseView, TemplateView):
    template_name = "manage_users.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs.get("product_slug")
        product = Product.objects.get(slug=slug)

        product_users = RoleService.get_product_members(product=product)

        context["product"] = product
        context["product_users"] = product_users

        return context


class PortalAddProductUserView(PortalBaseView):
    form_class = PortalProductRoleAssignmentForm
    template_name = "add_product_user.html"
    login_url = "sign_in"

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        if product_slug := self.kwargs.get("product_slug", None):
            kwargs.update(initial={"product": Product.objects.get(slug=product_slug)})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if context["search_result"]:
            return context

        slug = self.kwargs.get("product_slug")
        product = Product.objects.get(slug=slug)

        product_users = RoleService.get_product_members(product=product)

        context["product"] = product
        context["product_users"] = product_users

        return context

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            product = Product.objects.get(slug=kwargs.get("product_slug"))
            person = form.cleaned_data['person']
            role = form.cleaned_data['role']

            RoleService.assign_product_role(
                person=person,
                product=product,
                role=role
            )

            messages.success(request, "The user was successfully added!")

            self.success_url = reverse("portal:manage-users", args=(product.slug,))
            return redirect(self.success_url)

        return super().post(request, *args, **kwargs)

class PortalDashboardView(PortalBaseView, TemplateView):
    template_name = "main.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_template'] = 'dashboard.html'
        return context


class PortalReviewWorkView(LoginRequiredMixin, ListView):
    """View for reviewing submitted work in the portal."""
    model = BountyDeliveryAttempt
    context_object_name = "bounty_deliveries"
    template_name = "review_work.html"
    login_url = "sign_in"


class PortalContributorAgreementTemplateListView(LoginRequiredMixin, ListView):
    """View for managing contributor agreement templates in the portal."""
    model = ProductContributorAgreementTemplate
    context_object_name = "contributor_agreement_templates"
    login_url = "sign_in"
    template_name = "contributor_agreement_templates.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs.get("product_slug")
        context.update({
            "product": get_object_or_404(Product, slug=slug)
        })
        return context

    def get_queryset(self):
        product_slug = self.kwargs.get("product_slug")
        return ProductContributorAgreementTemplate.objects.filter(
            product__slug=product_slug
        ).order_by("-created_at")


class PortalProductBountyFilterView(LoginRequiredMixin, TemplateView):
    """View for filtering and displaying bounties in the portal."""
    template_name = "product_bounties.html"
    login_url = "sign_in"

    def get(self, request, *args, **kwargs):
        context = {}
        queryset = Bounty.objects.filter(
            challenge__product__slug=kwargs.get("product_slug")
        ).exclude(
            challenge__status=Challenge.ChallengeStatus.DRAFT
        )

        if query_parameter := request.GET.get("q"):
            for q in query_parameter.split(" "):
                q = q.split(":")
                key = q[0]
                if key == "sort":
                    value = q[1]

                    if value == "points-asc":
                        queryset = queryset.order_by("points")
                    elif value == "points-desc":
                        queryset = queryset.order_by("-points")

        if query_parameter := request.GET.get("search-bounty"):
            queryset = Bounty.objects.filter(
                challenge__title__icontains=query_parameter
            )

        context.update({"bounties": queryset})
        return render(request, self.template_name, context)


class PortalProductBountiesView(LoginRequiredMixin, ListView):
    """View for managing product bounties in the portal."""
    model = BountyClaim
    template_name = "product_bounties.html"
    context_object_name = "bounty_claims"
    login_url = "sign_in"

    def get_queryset(self):
        product_slug = self.kwargs.get("product_slug")
        product = Product.objects.get(slug=product_slug)
        return BountyClaim.objects.filter(
            bounty__challenge__product=product,
            status=BountyClaim.Status.REQUESTED,
        )

class PortalProductChallengesView(LoginRequiredMixin, ListView):
    model = Challenge
    context_object_name = "challenges"
    login_url = "sign_in"
    template_name = "manage_challenges.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        slug = self.kwargs.get("product_slug")
        context.update({"product": Product.objects.get(slug=slug)})
        return context

    def get_queryset(self):
        product_slug = self.kwargs.get("product_slug")
        return Challenge.objects.filter(product__slug=product_slug).order_by("-created_at")

class PortalProductChallengeFilterView(View):
    template_name = 'manage_challenges.html'
    
    def get(self, request, product_slug):
        product = get_object_or_404(Product, slug=product_slug)
        search_query = request.GET.get('search-challenge', '')
        sort = request.GET.get('sort', '')
        
        challenges = product.challenges.all()
        
        if search_query:
            challenges = challenges.filter(title__icontains=search_query)
            
        if sort == 'created-desc':
            challenges = challenges.order_by('-created_at')
        elif sort == 'created-asc':
            challenges = challenges.order_by('created_at')
            
        context = {
            'product': product,
            'challenges': challenges,
        }
        
        return render(request, self.template_name, context)


class PortalProductDetailView(LoginRequiredMixin, View):
    def get(self, request, slug):
        product = get_object_or_404(Product, slug=slug)
        tab = request.GET.get('tab', 'challenges')
        products = Product.objects.all()
        
        context = {
            'product': product,
            'current_product': product,
            'products': products,
            'active_tab': tab,
        }
        
        # Add tab-specific context
        if tab == 'settings':
            form = ProductSettingsForm(instance=product)
            context['form'] = form
        
        # Map tabs to their template names
        tab_templates = {
            'challenges': 'challenge_table.html',
            'bounty-claim-requests': 'bounty_claim_requests.html',
            'review-work': 'review_work.html',
            'contribution-agreements': 'contributor_agreement_templates.html',
            'user-management': 'manage_users.html',
            'settings': 'product_settings.html'
        }
        
        context['tab_template'] = tab_templates.get(tab, 'challenge_table.html')
        
        return render(request, 'product_detail.html', context)


class DeleteBountyClaimView(LoginRequiredMixin, DeleteView):
    """View for cancelling bounty claims from the portal."""
    model = BountyClaim
    login_url = "sign_in"
    success_url = reverse_lazy("portal:bounty-requests")

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        instance = BountyClaim.objects.get(pk=self.object.pk)
        if instance.status == BountyClaim.Status.REQUESTED:
            instance.status = BountyClaim.Status.CANCELLED
            instance.save()
            messages.success(request, "The bounty claim is successfully deleted.")
        else:
            messages.error(
                request,
                "Only the active claims can be deleted. The bounty claim did not deleted.",
            )

        return redirect(self.success_url)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        instance = BountyClaim.objects.get(pk=self.object.pk)
        if instance.status == BountyClaim.Status.REQUESTED:
            instance.status = BountyClaim.Status.CANCELLED
            instance.save()

        context = self.get_context_data()
        context["bounty"] = self.object.bounty
        context["elem"] = instance

        template_name = self.request.POST.get("from")
        if template_name == "bounty_detail_table.html":
            return render(
                request,
                "portal/partials/buttons/create_bounty_claim_button.html",
                context,
            )

        return super().post(request, *args, **kwargs)

def product_detail(request, slug, tab):
    context = {
        'product': get_object_or_404(Product, slug=slug),
        'default_tab': tab,
        'content_template': 'product_detail.html'  # or whatever your content template is
    }
    
    # Add any other context data you need
    if hasattr(request.user, 'person'):
        context['person'] = request.user.person
        
    # Get all products user has access to
    user_products = RoleService.get_user_products(person=context['person'])
    context['products'] = user_products
    
    if request.headers.get('HX-Request'):
        # Return just the content template
        return render(request, 'product_detail.html', context)
    
    # Return the full portal layout
    return render(request, 'main.html', context)

def get(self, request):
    context = {
        'person': getattr(request.user, 'person', None),
        'products': Product.objects.filter(owner=request.user),
        'content_template': 'dashboard.html'
    }
    return render(request, 'main.html', context)

class CreateAgreementTemplateView(LoginRequiredMixin, CreateView):
    template_name = 'create_agreement_template.html'
    # Add your model and form class here
    # model = ContributorAgreementTemplate
    # form_class = ContributorAgreementTemplateForm
    
    def get_success_url(self):
        return reverse('portal:product-detail', args=[self.kwargs['product_slug']]) + '?tab=agreements'
    
    def form_valid(self, form):
        form.instance.product = get_object_or_404(Product, slug=self.kwargs['product_slug'])
        return super().form_valid(form)