import json
from typing import Any, Dict
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, HttpResponse
from django.urls import reverse, reverse_lazy
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.core.exceptions import BadRequest
from django.views.generic import (
    ListView,
    TemplateView,
    RedirectView,
    FormView,
    CreateView,
    UpdateView,
    DeleteView,
    DetailView,
)

from .forms import (
    BountyClaimForm,
    IdeaForm,
    ProductForm,
    OrganisationForm,
    ChallengeForm,
    BountyForm,
)
from talent.models import BountyClaim
from .models import (
    Challenge,
    Product,
    Initiative,
    Bounty,
    Capability,
    Idea,
    Skill,
    Expertise,
)
from commerce.models import Organisation
from security.models import ProductRoleAssignment
from openunited.mixins import HTMXInlineFormValidationMixin


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

        product = get_object_or_404(Product, slug=self.kwargs.get("product_slug", None))

        context.update(
            {
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
                "product": product,
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
        bounty_claim = BountyClaim.objects.filter(
            bounty=bounty,
            kind__in=[BountyClaim.CLAIM_TYPE_DONE, BountyClaim.CLAIM_TYPE_ACTIVE],
        ).first()
        bounty_claims = BountyClaim.objects.filter(
            bounty=bounty, person=self.request.user.person
        )

        context.update(
            {
                "challenge": challenge,
                "bounty": bounty,
                "bounty_claim_form": BountyClaimForm(),
                "bounty_claim": bounty_claim,
                "current_user_created_claim_request": bounty_claims.count() > 0,
            }
        )

        if bounty_claim:
            context.update({"is_claimed": True, "claimed_by": bounty_claim.person})
        else:
            context.update({"is_claimed": False})

        return context


class InitiativeDetailView(BaseProductDetailView, TemplateView):
    template_name = "product_management/initiative_detail.html"


class CapabilityDetailView(BaseProductDetailView, TemplateView):
    template_name = "product_management/capability_detail.html"


# TODO: refactor this view
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
        self.success_url = request.headers.get("Hx-Current-Url")
        if url:
            url = url.split("/")
            challenge_id = url[-1]
            ch = Challenge.objects.get(id=challenge_id)
            bounty_claim = BountyClaim(
                bounty=ch.bounty_set.all().first(),
                person=request.user.person,
                kind=BountyClaim.CLAIM_TYPE_IN_REVIEW,
            )
            bounty_claim.save()
            messages.success(request, "Your bounty claim request is successfully sent!")

            return redirect(self.success_url)

        return super().post(request, *args, **kwargs)


class CreateProductView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = "product_management/create_product.html"
    login_url = "sign-up"

    def _is_htmx_request(self, request):
        htmx_header = request.headers.get("Hx-Request", None)
        return htmx_header == "true"

    # TODO: save the image and the documents
    # TODO: move the owner validation to forms
    # TODO: replace self.request with request
    def post(self, request, *args, **kwargs):
        if self._is_htmx_request(self.request):
            return super().post(request, *args, **kwargs)

        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            instance = form.save(commit=False)

            make_me_owner = form.cleaned_data.get("make_me_owner")
            organisation = form.cleaned_data.get("organisation")
            if make_me_owner and organisation:
                form.add_error(
                    "organisation",
                    "A product cannot be owned by a person and an organisation",
                )
                return render(request, self.template_name, context={"form": form})

            if not make_me_owner and not organisation:
                form.add_error("organisation", "You have to select an owner")
                return render(request, self.template_name, context={"form": form})

            if make_me_owner:
                instance.content_type = ContentType.objects.get_for_model(
                    request.user.person
                )
                instance.object_id = request.user.id
            else:
                instance.content_type = ContentType.objects.get_for_model(organisation)
                instance.object_id = organisation.id

            instance.save()

            _ = ProductRoleAssignment.objects.create(
                person=self.request.user.person,
                product=instance,
                role=ProductRoleAssignment.PRODUCT_ADMIN,
            )
            self.success_url = reverse("product_summary", args=(instance.slug,))
            return redirect(self.success_url)

        return super().post(request, *args, **kwargs)


class UpdateProductView(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "product_management/update_product.html"
    login_url = "sign-up"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.form_class(request.POST, request.FILES, instance=self.object)
        if form.is_valid():
            instance = form.save()
            self.success_url = reverse("product_summary", args=(instance.slug,))
            return redirect(self.success_url)

        return super().post(request, *args, **kwargs)


class CreateOrganisationView(
    LoginRequiredMixin, HTMXInlineFormValidationMixin, CreateView
):
    model = Organisation
    form_class = OrganisationForm
    template_name = "product_management/create_organisation.html"
    success_url = reverse_lazy("create-product")
    login_url = "sign-up"

    def post(self, request, *args, **kwargs):
        if self._is_htmx_request(self.request):
            return super().post(request, *args, **kwargs)

        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            form.save()

            return redirect(self.success_url)

        return super().post(request, *args, **kwargs)


class CreateChallengeView(
    LoginRequiredMixin, HTMXInlineFormValidationMixin, CreateView
):
    model = Challenge
    form_class = ChallengeForm
    template_name = "product_management/create_challenge.html"
    login_url = "sign-up"

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.created_by = request.user.person
            instance.save()

            messages.success(request, _("The challenge is successfully created!"))
            self.success_url = reverse(
                "challenge_detail",
                args=(
                    instance.product.slug,
                    instance.id,
                ),
            )
            return redirect(self.success_url)

        return super().post(request, *args, **kwargs)


class DashboardBaseView(LoginRequiredMixin):
    login_url = "sign_in"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        person = self.request.user.person
        photo_url, _ = person.get_photo_url()
        product_queryset = Product.objects.filter(
            content_type__model="person", object_id=person.id
        )
        context.update(
            {
                "person": person,
                "photo_url": photo_url,
                "products": product_queryset,
            }
        )
        return context


class DashboardView(DashboardBaseView, TemplateView):
    template_name = "product_management/dashboard.html"


class DashboardHomeView(DashboardBaseView, TemplateView):
    template_name = "product_management/dashboard/dashboard_home.html"


class ManageBountiesView(DashboardBaseView, TemplateView):
    template_name = "product_management/dashboard/my_bounties.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        person = self.request.user.person
        queryset = BountyClaim.objects.filter(person=person)
        context.update({"bounty_claims": queryset})
        return context


class DashboardBountyClaimRequestsView(LoginRequiredMixin, ListView):
    model = BountyClaim
    context_object_name = "bounty_claims"
    template_name = "product_management/dashboard/bounty_claim_requests.html"
    login_url = "sign_in"

    def get_queryset(self):
        person = self.request.user.person
        queryset = BountyClaim.objects.filter(person=person)
        return queryset


class DashboardBountyClaimsView(TemplateView):
    template_name = "product_management/dashboard/accepted_bounty_claims.html"


class DashboardProductDetailView(DashboardBaseView, DetailView):
    model = Product
    template_name = "product_management/dashboard/product_detail.html"

    def get_object(self, queryset=None):
        slug = self.kwargs.get("product_slug")
        return get_object_or_404(self.model, slug=slug)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"challenges": Challenge.objects.filter(product=self.object)})
        return context


class DashboardProductChallengesView(LoginRequiredMixin, ListView):
    model = Challenge
    paginate_by = 20
    context_object_name = "challenges"
    login_url = "sign_in"
    template_name = "product_management/dashboard/manage_challenges.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        slug = self.kwargs.get("product_slug")
        context.update({"product": Product.objects.get(slug=slug)})
        return context

    def get_queryset(self):
        product_slug = self.kwargs.get("product_slug")
        queryset = Challenge.objects.filter(product__slug=product_slug)
        return queryset


class DashboardProductChallengeFilterView(LoginRequiredMixin, TemplateView):
    template_name = "product_management/dashboard/challenge_table.html"
    login_url = "sign_in"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        slug = self.kwargs.get("product_slug")
        context.update({"product": Product.objects.get(slug=slug)})
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()

        product = context.get("product")
        queryset = Challenge.objects.filter(product=product)

        # Handle sort filter
        query_parameter = request.GET.get("q")
        if query_parameter:
            for q in query_parameter.split(" "):
                q = q.split(":")
                key = q[0]
                value = q[1]

                if key == "sort":
                    if value == "created-asc":
                        queryset = queryset.order_by("created_at")
                    if value == "created-desc":
                        queryset = queryset.order_by("-created_at")

        # Handle search
        query_parameter = request.GET.get("search-challenge")
        if query_parameter:
            queryset = Challenge.objects.filter(title__icontains=query_parameter)

        context.update({"challenges": queryset})

        return render(request, self.template_name, context)


class DashboardProductBountiesView(LoginRequiredMixin, ListView):
    model = Bounty
    context_object_name = "bounty_claims"
    template_name = "product_management/dashboard/manage_bounties.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        slug = self.kwargs.get("product_slug")
        context.update({"product": Product.objects.get(slug=slug)})
        return context

    def get_queryset(self):
        product_slug = self.kwargs.get("product_slug")
        product = Product.objects.get(slug=product_slug)
        queryset = BountyClaim.objects.filter(
            bounty__challenge__product=product, kind=BountyClaim.CLAIM_TYPE_IN_REVIEW
        )
        return queryset


class DashboardProductBountyFilterView(LoginRequiredMixin, TemplateView):
    template_name = "product_management/dashboard/bounty_table.html"
    login_url = "sign_in"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        slug = self.kwargs.get("product_slug")
        context.update({"product": Product.objects.get(slug=slug)})
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()

        product = context.get("product")
        queryset = Bounty.objects.filter(challenge__product=product)

        # Handle sort filter
        query_parameter = request.GET.get("q")
        if query_parameter:
            for q in query_parameter.split(" "):
                q = q.split(":")
                key = q[0]
                value = q[1]

                if key == "sort":
                    if value == "points-asc":
                        queryset = queryset.order_by("points")
                    if value == "points-desc":
                        queryset = queryset.order_by("-points")

        # Handle search
        query_parameter = request.GET.get("search-bounty")
        if query_parameter:
            queryset = Bounty.objects.filter(
                challenge__title__icontains=query_parameter
            )

        context.update({"bounties": queryset})

        return render(request, self.template_name, context)


# This view displays the each action of a product manager does, kinda like logs.
# TODO: change this view with ListView after History model is created
class DashboardProductHistoryView(LoginRequiredMixin, TemplateView):
    template_name = "product_management/dashboard/action_history.html"


class UpdateChallengeView(
    LoginRequiredMixin, HTMXInlineFormValidationMixin, UpdateView
):
    model = Challenge
    form_class = ChallengeForm
    template_name = "product_management/update_challenge.html"
    login_url = "sign-up"

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)

        instance = kwargs.get("instance")
        kwargs.update({"initial": {"product": instance.product.pk}})
        return kwargs

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.form_class(request.POST, instance=self.object)
        if form.is_valid():
            instance = form.save()
            messages.success(request, _("The challenge is successfully updated!"))

            self.success_url = reverse(
                "challenge_detail",
                args=(
                    instance.product.slug,
                    instance.id,
                ),
            )
            return redirect(self.success_url)

        return super().post(request, *args, **kwargs)


class DeleteChallengeView(LoginRequiredMixin, DeleteView):
    model = Challenge
    template_name = "product_management/delete_challenge.html"
    login_url = "sign-up"
    success_url = reverse_lazy("challenges")

    def get(self, request, *args, **kwargs):
        challenge_obj = self.get_object()
        if challenge_obj.can_delete_challenge(request.user.person):
            Challenge.objects.get(pk=challenge_obj.pk).delete()
            messages.success(request, _("The challenge is successfully deleted!"))
            return redirect(self.success_url)
        else:
            messages.error(
                request, _("You do not have rights to remove this challenge.")
            )

            return redirect(
                reverse(
                    "challenge_detail",
                    args=(
                        challenge_obj.product.slug,
                        challenge_obj.pk,
                    ),
                )
            )


class CreateBountyView(LoginRequiredMixin, CreateView):
    model = Bounty
    form_class = BountyForm
    template_name = "product_management/create_bounty.html"
    login_url = "sign-up"

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            challenge = form.cleaned_data.get("challenge")
            instance.challenge = challenge
            skill_id = form.cleaned_data.get("selected_skill_ids")[0]
            instance.skill = Skill.objects.get(id=skill_id)
            instance.save()

            instance.expertise.add(
                *Expertise.objects.filter(
                    id__in=form.cleaned_data.get("selected_expertise_ids")
                )
            )
            instance.save()

            self.success_url = reverse(
                "challenge_detail",
                args=(challenge.product.slug, challenge.pk),
            )

            return redirect(self.success_url)

        return super().post(request, *args, **kwargs)


class UpdateBountyView(LoginRequiredMixin, UpdateView):
    model = Bounty
    form_class = BountyForm
    template_name = "product_management/create_bounty.html"
    login_url = "sign-up"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.form_class(request.POST, instance=self.object)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.challenge = form.cleaned_data.get("challenge")
            skill_id = form.cleaned_data.get("selected_skill_ids")[0]
            instance.skill = Skill.objects.get(id=skill_id)
            instance.save()

            instance.expertise.add(
                *Expertise.objects.filter(
                    id__in=form.cleaned_data.get("selected_expertise_ids")
                )
            )
            instance.save()

            self.success_url = reverse(
                "challenge_detail",
                args=(self.object.challenge.product.slug, self.object.challenge.id),
            )
            return redirect(self.success_url)

        return super().post(request, *args, **kwargs)


class DeleteBountyView(LoginRequiredMixin, DeleteView):
    model = Bounty
    login_url = "sign-up"
    success_url = reverse_lazy("challenges")

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        Bounty.objects.get(pk=self.object.pk).delete()
        return redirect(self.success_url)


class DeleteBountyClaimView(LoginRequiredMixin, DeleteView):
    model = BountyClaim
    login_url = "sign_in"
    success_url = reverse_lazy("dashboard-bounty-requests")

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        instance = BountyClaim.objects.get(pk=self.object.pk)
        if instance.kind == BountyClaim.CLAIM_TYPE_IN_REVIEW:
            instance.delete
            messages.success(request, _("The bounty claim is successfully deleted."))
        else:
            messages.error(
                request,
                _(
                    "Only the active claims can be deleted. The bounty claim did not deleted."
                ),
            )

        return redirect(self.success_url)


def bounty_claim_actions(request, pk):
    instance = BountyClaim.objects.get(pk=pk)
    action_type = request.GET.get("action")
    if action_type == "accept":
        instance.kind = BountyClaim.CLAIM_TYPE_ACTIVE

        # If one claim is accepted for a particular challenge, the other claims automatically fails.
        challenge = instance.bounty.challenge
        _ = BountyClaim.objects.filter(bounty__challenge=challenge).update(
            kind=BountyClaim.CLAIM_TYPE_FAILED
        )
    elif action_type == "reject":
        instance.kind = BountyClaim.CLAIM_TYPE_FAILED
    else:
        raise BadRequest()

    instance.save()

    return redirect(
        reverse(
            "dashboard-product-bounties", args=(instance.bounty.challenge.product.slug,)
        )
    )
