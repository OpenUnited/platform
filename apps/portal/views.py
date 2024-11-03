"""
Views for the product management portal.

This module handles the presentation layer for product management portal features,
including the portal overview, work review, bounty management, and contributor agreements.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, TemplateView, DeleteView, UpdateView
from django.shortcuts import get_object_or_404, render, redirect
from django.db import models
from django.urls import reverse, reverse_lazy
from django.db.models import Count, Q
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.http import HttpResponseBadRequest
from django.core.exceptions import BadRequest

from apps.capabilities.product_management.models import (
    Product,
    ProductContributorAgreementTemplate,
    Bounty,
    Challenge,
)
from apps.capabilities.security.models import ProductRoleAssignment
from apps.capabilities.talent.models import BountyClaim, BountyDeliveryAttempt
from apps.capabilities.security.services import RoleService
from apps.capabilities.product_management import forms
from apps.common import mixins as common_mixins


class PortalBaseView(LoginRequiredMixin, TemplateView):
    """Base view for portal pages with common functionality."""
    login_url = "sign_in"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if not hasattr(user, 'person'):
            return context
            
        person = user.person
        managed_products = RoleService.get_managed_products(
            person=person
        )
        
        context.update({
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


class PortalProductSettingView(LoginRequiredMixin, common_mixins.AttachmentMixin, UpdateView):
    model = Product
    form_class = forms.ProductForm
    template_name = "product_settings.html"
    login_url = "sign_in"

    def get_success_url(self):
        return reverse("portal:product-settings", args=(self.object.id,))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        initial = {}
        
        # Check if product is owned by current user
        if self.object.is_owned_by_person():
            initial_make_me_owner = self.object.person_id == self.request.user.person.id
            initial = {"make_me_owner": initial_make_me_owner}
            context["make_me_owner"] = initial_make_me_owner

        # Check if product is owned by an organisation
        if self.object.is_owned_by_organisation():
            initial = {"organisation": self.object.organisation}
            context["organisation"] = self.object.organisation

        context["form"] = self.form_class(instance=self.object, initial=initial)
        context["product_instance"] = self.object
        return context

    def form_valid(self, form):
        return super().form_save(form)

    def form_invalid(self, form):
        print(form.errors)  # Consider using proper logging instead of print
        return super().form_invalid(form)
    

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
    form_class = forms.ProductRoleAssignmentForm
    template_name = "update_product_user.html"
    login_url = "sign_in"
    context_object_name = "product_role_assignment"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context["search_result"]:
            return context

        slug = self.kwargs.get("product_slug")
        product = Product.objects.get(slug=slug)
        product_users = RoleService.get_product_role_assignments(product=product)

        context["product"] = product
        context["product_users"] = product_users

        return context

    def post(self, request, *args, **kwargs):
        product_role_assignment = ProductRoleAssignment.objects.get(pk=kwargs.get("pk"))
        product = Product.objects.get(slug=kwargs.get("product_slug"))

        form = forms.ProductRoleAssignmentForm(request.POST, instance=product_role_assignment)

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

        product_users = RoleService.get_product_role_assignments(product=product)

        context["product"] = product
        context["product_users"] = product_users

        return context


class PortalAddProductUserView(PortalBaseView):
    form_class = forms.ProductRoleAssignmentForm
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

        product_users = RoleService.get_product_role_assignments(product=product)

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

class PortalDashboardView(PortalBaseView):
    template_name = "main.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get products for the current user
        person = self.request.user.person
        
        # Get products from RoleService (since you're using it elsewhere)
        products = RoleService.get_managed_products(person=person)
        
        # Add to context
        context.update({
            "portal_url": reverse("portal:home"),
            "products": products,
            "default_tab": kwargs.get('default_tab', 1),
            "active_bounty_claims": BountyClaim.objects.filter(
                person=person,
                status__in=[BountyClaim.Status.GRANTED, BountyClaim.Status.REQUESTED]
            )
        })
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

class PortalProductChallengeFilterView(LoginRequiredMixin, TemplateView):
    """View for filtering and displaying challenges in the portal."""
    template_name = "challenge_table.html"
    login_url = "sign_in"

    def get(self, request, *args, **kwargs):
        context = {}
        queryset = Challenge.objects.filter(
            product__slug=kwargs.get("product_slug")
        ).annotate(
            total_bounties=Count("bounty", filter=Q(bounty__is_active=True))
        )

        if query_parameter := request.GET.get("q"):
            for q in query_parameter.split(" "):
                q = q.split(":")
                key = q[0]
                if key == "sort":
                    value = q[1]

                    if value == "bounties-asc":
                        queryset = queryset.order_by("total_bounties")
                    elif value == "bounties-desc":
                        queryset = queryset.order_by("-total_bounties")

        if query_parameter := request.GET.get("search-challenge"):
            queryset = Challenge.objects.filter(
                title__icontains=query_parameter
            )

        context.update({"challenges": queryset})
        return render(request, self.template_name, context)


class PortalProductDetailView(PortalBaseView):
    """Detailed view of a product in the portal overview."""
    template_name = "product_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product_slug = self.kwargs.get("product_slug")
        default_tab = self.kwargs.get("default_tab", 1)

        # Get the product object
        product = get_object_or_404(Product, slug=product_slug)
        
        context.update({
            "portal_url": reverse("portal:product-detail", args=(product_slug, default_tab)),
            "default_tab": default_tab,
            "product_slug": product_slug,
            "product": product,
            "product_challenges": product.challenge_set.all(),
            "product_bounties": Bounty.objects.filter(challenge__product=product),
        })
        
        return context


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