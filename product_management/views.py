from typing import Any, Dict
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, HttpResponse
from django.urls import reverse
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render
from django.views.generic import (
    ListView,
    TemplateView,
    RedirectView,
    FormView,
    CreateView,
    UpdateView,
    DetailView,
)

from .forms import BountyClaimForm, IdeaForm, ProductForm
from talent.models import BountyClaim
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


# If the user is not authenticated, we redirect him to the sign up page using LoginRequiredMixing.
# After he signs in, we should redirect him with the help of redirect_field_name attribute
# See for more detail: https://docs.djangoproject.com/en/4.2/topics/auth/default/
class CreateProductIdea(LoginRequiredMixin, BaseProductDetailView, CreateView):
    login_url = "sign-up"
    template_name = "product_management/add_product_idea.html"
    form_class = IdeaForm

    def post(self, request, *args, **kwargs):
        form = IdeaForm(request.POST)

        if form.is_valid():
            person = self.request.user.person
            product = Product.objects.get(slug=kwargs.get("product_slug"))

            idea = form.save(commit=False)
            idea.person = person
            idea.product = product
            idea.save()

            return redirect("product_ideas_bugs", **kwargs)

        return super().post(request, *args, **kwargs)


class UpdateProductIdea(LoginRequiredMixin, BaseProductDetailView, UpdateView):
    login_url = "sign-up"
    template_name = "product_management/update_product_idea.html"
    model = Idea
    form_class = IdeaForm

    def get(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        idea_pk = kwargs.get("pk")
        idea = Idea.objects.get(pk=idea_pk)
        form = IdeaForm(request.GET, instance=idea)

        return super().get(request, *args, **kwargs)

    def post(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        idea_pk = kwargs.get("pk")
        idea = Idea.objects.get(pk=idea_pk)

        form = IdeaForm(request.POST, instance=idea)

        if form.is_valid():
            form.save()

            return redirect("product_idea_detail", **kwargs)

        return super().post(request, *args, **kwargs)


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


class ProductIdeaDetail(BaseProductDetailView, DetailView):
    template_name = "product_management/product_idea_detail.html"
    model = Idea
    context_object_name = "idea"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(
            {
                "pk": self.object.pk,
            }
        )

        return context


# TODO: note that id's must be related to products. For product1, challenges must start from 1. For product2, challenges must start from 1 etc.
class ChallengeDetailView(BaseProductDetailView, TemplateView):
    template_name = "product_management/challenge_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        challenge_id = context.get("challenge_id")
        challenge = get_object_or_404(Challenge, id=challenge_id)
        bounty = challenge.bounty_set.all().first()
        bounty_claim = (
            BountyClaim.objects.filter(bounty=bounty)
            .exclude(kind=BountyClaim.CLAIM_TYPE_FAILED)
            .first()
        )

        context.update(
            {
                "challenge": challenge,
                "bounty_claim_form": BountyClaimForm(),
                "bounty_claim": bounty_claim,
            }
        )

        return context


class InitiativeDetailView(BaseProductDetailView, TemplateView):
    template_name = "product_management/initiative_detail.html"


class CapabilityDetailView(BaseProductDetailView, TemplateView):
    template_name = "product_management/capability_detail.html"


class BountyClaimView(FormView):
    form_class = BountyClaimForm
    template_name = "product_management/bounty_claim_form.html"

    def get(self, request, *args, **kwargs):
        is_triggered_by_cancel_button = request.GET.get("claim-cancel-button")
        if is_triggered_by_cancel_button:
            return HttpResponse("")

        return self.render_to_response(self.get_context_data(form=BountyClaimForm()))

    def post(self, request, *args, **kwargs):
        url = request.headers.get("Hx-Current-Url")
        if url:
            url = url.split("/")
            challenge_id = url[-1]
            ch = Challenge.objects.get(id=challenge_id)
            bounty_claim = BountyClaim(
                bounty=ch.bounty_set.all().first(), person=request.user.person
            )
            bounty_claim.save()

        self.success_url = request.headers.get("Hx-Current-Url")
        return super().post(request, *args, **kwargs)


class CreateProductView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = "product_management/create_product.html"
    login_url = "sign-up"

    # TODO: save the image and the documents
    def post(self, request, *args, **kwargs):
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            name = form.cleaned_data.get("name")
            error = Product.check_slug_from_name(name)
            if error:
                form.add_error("name", error)
                return render(request, self.template_name, context={"form": form})

            instance = form.save()
            _ = ProductRoleAssignment.objects.create(
                person=self.request.user.person, product=instance, role=2
            )
            self.success_url = reverse(
                "product_summary", args=("organisation_username_four", instance.slug)
            )
            return redirect(self.success_url)

        return super().post(request, *args, **kwargs)
