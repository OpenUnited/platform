from typing import Any, Dict
from django.shortcuts import redirect
from django.urls import reverse
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.db import models
from django.views.generic import ListView, TemplateView, RedirectView

from .models import Challenge, Product, Initiative, Bounty, Capability, Idea
from commerce.models import Organisation
from security.models import ProductRoleAssignment


class ChallengeListView(ListView):
    model = Challenge
    context_object_name = "challenges"
    template_name = "product_management/challenges.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["request"] = self.request

        return context

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        return response


class ProductListView(ListView):
    model = Product
    context_object_name = "products"
    queryset = Product.objects.filter(is_private=False)
    template_name = "product_management/products.html"

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        return response


class BaseProductDetailView:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        organisation = get_object_or_404(
            Organisation, username=self.kwargs["organisation_username"]
        )
        product = get_object_or_404(Product, slug=self.kwargs["product_slug"])

        context.update(
            {
                "organisation": organisation,
                "organisation_username": organisation.username,
                "product": product,
                "product_slug": product.slug,
            }
        )

        return context


class ProductRedirectView(BaseProductDetailView, RedirectView):
    def get(self, request, *args, **kwargs):
        url = reverse("product_summary", kwargs=kwargs)

        return redirect(url)


class ProductSummaryView(BaseProductDetailView, TemplateView):
    template_name = "product_management/product_summary.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = context["product"]
        challenges = Challenge.objects.filter(product=product)
        context.update(
            {
                "challenges": challenges,
                "capabilities": Capability.get_root_nodes(),
            }
        )
        return context


class ProductChallengesView(BaseProductDetailView, TemplateView):
    template_name = "product_management/product_challenges.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        product = context["product"]
        challenges = Challenge.objects.filter(product=product)
        context.update(
            {
                "challenges": challenges,
            }
        )

        return context


class ProductInitiativesView(BaseProductDetailView, TemplateView):
    template_name = "product_management/product_initiatives.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        product = context["product"]
        initiatives = Initiative.objects.filter(product=product)

        # Query to calculate total points for each Initiative, considering only active Bounties with status "Available"
        initiatives = initiatives.annotate(
            total_points=Sum(
                "challenge__bounty__points",
                filter=models.Q(
                    challenge__bounty__status=Bounty.BOUNTY_STATUS_AVAILABLE
                )
                & models.Q(challenge__bounty__is_active=True),
            )
        )

        context.update(
            {
                "initiatives": initiatives,
            }
        )

        return context


class ProductTreeView(BaseProductDetailView, TemplateView):
    template_name = "product_management/product_tree.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(
            {
                "capabilities": Capability.get_root_nodes(),
            }
        )

        return context


class ProductIdeasAndBugsView(BaseProductDetailView, TemplateView):
    template_name = "product_management/product_ideas.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = context["product"]

        context.update({"ideas": Idea.objects.filter(product=product), "bugs": []})

        return context


class ProductRoleAssignmentView(BaseProductDetailView, TemplateView):
    template_name = "product_management/product_people.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = context["product"]

        context.update(
            {
                "product_people": ProductRoleAssignment.objects.filter(product=product),
            }
        )

        return context


# TODO: note that id's must be related to products. For product1, challenges must start from 1. For product2, challenges must start from 1 etc.
class ChallengeDetailView(BaseProductDetailView, TemplateView):
    template_name = "product_management/challenge_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        challenge_id = context.get("challenge_id")

        context.update({"challenge": get_object_or_404(Challenge, id=challenge_id)})

        return context


class InitiativeDetailView(BaseProductDetailView, TemplateView):
    template_name = "product_management/initiative_detail.html"


class CapabilityDetailView(BaseProductDetailView, TemplateView):
    template_name = "product_management/capability_detail.html"
