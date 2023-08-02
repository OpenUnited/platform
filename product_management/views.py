from django.shortcuts import HttpResponse, render, redirect
from django.urls import reverse
from django.db.models import Sum
from django.db import models
from django.views.generic import ListView

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


def challenge_detail(request, organisation_username, product_slug, challenge_id):
    # check if the organisation, product and challenge exist
    return render(request, "product_management/challenge_detail.html")


class ProductListView(ListView):
    model = Product
    context_object_name = "products"
    template_name = "product_management/products.html"

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        return response


def product_redirect(request, organisation_username, product_slug):
    kwargs = {
        "organisation_username": organisation_username,
        "product_slug": product_slug,
    }
    url = reverse("product_summary", kwargs=kwargs)

    return redirect(url)


def product_detail(request, organisation_username, product_slug):
    return render(
        request,
        "product_management/product_detail_base.html",
        context={
            "organisation_username": organisation_username,
            "product_slug": product_slug,
        },
    )


def product_summary(request, organisation_username, product_slug):
    product = Product.objects.get(slug=product_slug)
    challenges = Challenge.objects.filter(product=product)

    return render(
        request,
        "product_management/product_summary.html",
        context={
            "organisation_username": organisation_username,
            "product_slug": product_slug,
            "product": product,
            "challenges": challenges,
            "capabilities": Capability.get_root_nodes(),
        },
    )


def product_initiatives(request, organisation_username, product_slug):
    product = Product.objects.get(slug=product_slug)
    initiatives = Initiative.objects.filter(product=product)

    # Query to calculate total points for each Initiative, considering only active Bounties with status "Available"
    initiatives = initiatives.annotate(
        total_points=Sum(
            "challenge__bounty__points",
            filter=models.Q(challenge__bounty__status=Bounty.BOUNTY_STATUS_AVAILABLE)
            & models.Q(challenge__bounty__is_active=True),
        )
    )

    return render(
        request,
        "product_management/product_initiatives.html",
        context={
            "organisation_username": organisation_username,
            "product_slug": product_slug,
            "product": product,
            "initiatives": initiatives,
        },
    )


def product_challenges(request, organisation_username, product_slug):
    product = Product.objects.get(slug=product_slug)
    challenges = Challenge.objects.filter(product=product)
    return render(
        request,
        "product_management/product_challenges.html",
        context={
            "organisation_username": organisation_username,
            "product_slug": product_slug,
            "challenges": challenges,
        },
    )


def product_tree(request, organisation_username, product_slug):
    return render(
        request,
        "product_management/product_tree.html",
        context={
            "organisation_username": organisation_username,
            "product_slug": product_slug,
            "capabilities": Capability.get_root_nodes(),
        },
    )


def product_ideas_bugs(request, organisation_username, product_slug):
    return render(
        request,
        "product_management/product_ideas.html",
        context={
            "organisation_username": organisation_username,
            "product_slug": product_slug,
        },
    )


def product_people(request, organisation_username, product_slug):
    return render(
        request,
        "product_management/product_people.html",
        context={
            "organisation_username": organisation_username,
            "product_slug": product_slug,
        },
    )


def initiative_details(request, organisation_username, product_slug, initiative_id):
    return HttpResponse(f"{organisation_username} - {product_slug} - {initiative_id}")


def capability_detail(request, organisation_username, product_slug, capability_id):
    return HttpResponse(
        f"TODO: Implement this page: {organisation_username} - {product_slug} - {capability_id}"
    )
