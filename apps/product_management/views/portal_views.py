"""
Views for the product management portal.

This module handles the presentation layer for product management portal features,
including the portal overview, work review, bounty management, and contributor agreements.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, TemplateView, DeleteView
from django.shortcuts import get_object_or_404, render, redirect
from django.db import models
from django.urls import reverse, reverse_lazy
from django.db.models import Count, Q
from django.core.exceptions import PermissionDenied
from django.contrib import messages

from apps.product_management.models import (
    Product,
    ProductContributorAgreementTemplate,
    Bounty,
    Challenge,
    BountyClaim
)
from apps.talent.models import BountyDeliveryAttempt
from apps.security.services import RoleService


class PortalBaseView(LoginRequiredMixin, TemplateView):
    """Base view for portal pages with common functionality."""
    login_url = "sign_in"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if not hasattr(user, 'person'):
            return context
            
        person = user.person
        managed_products = RoleService.get_products_with_role(
            person=person,
            role=RoleService.PRODUCT_MANAGER
        )
        
        context.update({
            "managed_products": managed_products,
            "person": person,
        })
        return context


class PortalDashboardView(PortalBaseView):
    """Dashboard view showing overview of managed products."""
    template_name = "product_management/portal/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not hasattr(self.request.user, 'person'):
            return context
            
        person = self.request.user.person
        managed_products = context.get("managed_products", [])

        if product_slug := self.kwargs.get("product_slug"):
            context["current_product"] = get_object_or_404(
                managed_products, slug=product_slug
            )
            context["portal_url"] = reverse(
                "portal-product-dashboard", args=(product_slug, 0)
            )
        else:
            context["portal_url"] = reverse("portal-dashboard")

        return context


class PortalReviewWorkView(LoginRequiredMixin, ListView):
    """View for reviewing submitted work in the portal."""
    model = BountyDeliveryAttempt
    context_object_name = "bounty_deliveries"
    template_name = "product_management/portal/review_work.html"
    login_url = "sign_in"


class PortalContributorAgreementTemplateListView(LoginRequiredMixin, ListView):
    """View for managing contributor agreement templates in the portal."""
    model = ProductContributorAgreementTemplate
    context_object_name = "contributor_agreement_templates"
    login_url = "sign_in"
    template_name = "product_management/portal/contributor_agreement_templates.html"

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
    template_name = "product_management/portal/product_bounties.html"
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
    template_name = "product_management/portal/product_bounties.html"
    context_object_name = "bounty_claims"
    login_url = "sign_in"

    def get_queryset(self):
        product_slug = self.kwargs.get("product_slug")
        product = Product.objects.get(slug=product_slug)
        return BountyClaim.objects.filter(
            bounty__challenge__product=product,
            status=BountyClaim.Status.REQUESTED,
        )


class PortalProductChallengeFilterView(LoginRequiredMixin, TemplateView):
    """View for filtering and displaying challenges in the portal."""
    template_name = "product_management/portal/product_challenges.html"
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
    template_name = "product_management/portal/product_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product_slug = self.kwargs.get("product_slug")
        managed_products = context.get("managed_products", [])

        try:
            current_product = managed_products.get(slug=product_slug)
        except Product.DoesNotExist:
            raise PermissionDenied(
                "You don't have permission to access this product's portal"
            )

        context.update({
            "current_product": current_product,
            "portal_url": reverse("portal-product", args=(product_slug,)),
        })
        return context


class DeleteBountyClaimView(LoginRequiredMixin, DeleteView):
    """View for cancelling bounty claims from the portal."""
    model = BountyClaim
    login_url = "sign_in"
    success_url = reverse_lazy("portal-bounty-requests")

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
                "product_management/partials/buttons/create_bounty_claim_button.html",
                context,
            )

        return super().post(request, *args, **kwargs)