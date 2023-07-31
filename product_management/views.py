from django.shortcuts import HttpResponse, render, redirect
from django.urls import reverse
from django.views.generic import ListView

from .models import Challenge, Product


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
    return HttpResponse(f"{organisation_username} {product_slug} {challenge_id}")


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
    return render(
        request,
        "product_management/product_summary.html",
        context={
            "organisation_username": organisation_username,
            "product_slug": product_slug,
            "product": product,
        },
    )


def product_initiatives(request, organisation_username, product_slug):
    return render(
        request,
        "product_management/product_detail_base.html",
        context={
            "organisation_username": organisation_username,
            "product_slug": product_slug,
        },
    )


def product_challenges(request, organisation_username, product_slug):
    return render(
        request,
        "product_management/product_detail_base.html",
        context={
            "organisation_username": organisation_username,
            "product_slug": product_slug,
        },
    )


def product_tree(request, organisation_username, product_slug):
    return render(
        request,
        "product_management/product_detail_base.html",
        context={
            "organisation_username": organisation_username,
            "product_slug": product_slug,
        },
    )


def product_ideas_bugs(request, organisation_username, product_slug):
    return render(
        request,
        "product_management/product_detail_base.html",
        context={
            "organisation_username": organisation_username,
            "product_slug": product_slug,
        },
    )


def product_people(request, organisation_username, product_slug):
    return render(
        request,
        "product_management/product_detail_base.html",
        context={
            "organisation_username": organisation_username,
            "product_slug": product_slug,
        },
    )
