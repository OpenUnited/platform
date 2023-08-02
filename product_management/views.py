from typing import Any, Dict
from django.shortcuts import HttpResponse, render, redirect
from django.urls import reverse
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.db import models
from django.views.generic import ListView, TemplateView

from .models import Challenge, Product, Initiative, Bounty, Capability


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
    template_name = "product_management/products.html"

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        return response


class BaseProductDetailView(TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(
            {
                "organisation_username": self.kwargs["organisation_username"],
                "product_slug": self.kwargs["product_slug"],
            }
        )

        return context


class ProductSummaryView(BaseProductDetailView):
    template_name = "product_management/product_summary.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = get_object_or_404(Product, slug=self.kwargs["product_slug"])
        challenges = Challenge.objects.filter(product=product)
        context.update(
            {
                "product": product,
                "challenges": challenges,
                "capabilities": Capability.get_root_nodes(),
            }
        )
        return context


class ProductChallengesView(BaseProductDetailView):
    template_name = "product_management/product_challenges.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        product = get_object_or_404(Product, slug=self.kwargs["product_slug"])
        challenges = Challenge.objects.filter(product=product)
        context.update(
            {
                "challenges": challenges,
            }
        )

        return context


class ProductInitiativesView(BaseProductDetailView):
    template_name = "product_management/product_initiatives.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        product = get_object_or_404(Product, slug=self.kwargs["product_slug"])
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
                "product": product,
                "initiatives": initiatives,
            }
        )

        return context


class ProductTreeView(BaseProductDetailView):
    template_name = "product_management/product_tree.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(
            {
                "capabilities": Capability.get_root_nodes(),
            }
        )

        print(context)

        return context


class ProductIdeasAndBugsView(BaseProductDetailView):
    template_name = "product_management/product_ideas.html"


class ProductPeopleView(BaseProductDetailView):
    template_name = "product_management/product_people.html"


def initiative_details(request, organisation_username, product_slug, initiative_id):
    return HttpResponse(f"{organisation_username} - {product_slug} - {initiative_id}")


def capability_detail(request, organisation_username, product_slug, capability_id):
    return HttpResponse(
        f"TODO: Implement this page: {organisation_username} - {product_slug} - {capability_id}"
    )


def challenge_detail(request, organisation_username, product_slug, challenge_id):
    # check if the organisation, product and challenge exist
    return render(request, "product_management/challenge_detail.html")


def product_redirect(request, organisation_username, product_slug):
    kwargs = {
        "organisation_username": organisation_username,
        "product_slug": product_slug,
    }
    url = reverse("product_summary", kwargs=kwargs)

    return redirect(url)
