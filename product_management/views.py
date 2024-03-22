from typing import Any, Dict
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, HttpResponse, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.db import models
from django.db.models import Q, Sum, Case, Value, When
from django.shortcuts import get_object_or_404, HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.core.exceptions import BadRequest, PermissionDenied
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
    BugForm,
    ProductForm,
    OrganisationForm,
    ChallengeForm,
    BountyForm,
    InitiativeForm,
    CapabilityForm,
    ProductAreaUpdateForm,
    ProductAreaCreateForm,
)
from talent.models import BountyClaim, BountyDeliveryAttempt
from .models import (
    Challenge,
    Product,
    Initiative,
    Bounty,
    Capability,
    Idea,
    Bug,
    Skill,
    Expertise,
    Attachment,
)
from commerce.models import Organisation
from security.models import ProductRoleAssignment
from openunited.mixins import HTMXInlineFormValidationMixin

from .filters import ChallengeFilter


class ChallengeListView(ListView):
    model = Challenge
    context_object_name = "challenges"
    template_name = "product_management/challenges.html"
    paginate_by = 8
    filterset_class = ChallengeFilter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["request"] = self.request
        context["filter"] = self.filterset_class(
            self.request.GET, queryset=self.get_queryset()
        )

        return context

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        return response

    def get_queryset(self):
        queryset = super().get_queryset()

        custom_order = Case(
            When(status=self.model.CHALLENGE_STATUS_AVAILABLE, then=Value(0)),
            When(status=self.model.CHALLENGE_STATUS_CLAIMED, then=Value(1)),
            When(status=self.model.CHALLENGE_STATUS_IN_REVIEW, then=Value(2)),
            When(status=self.model.CHALLENGE_STATUS_BLOCKED, then=Value(3)),
            When(status=self.model.CHALLENGE_STATUS_DONE, then=Value(4)),
        )
        queryset = queryset.annotate(custom_order=custom_order).order_by(
            "custom_order", "-id"
        )

        challenge_filter = self.filterset_class(
            self.request.GET, queryset=queryset
        )
        return challenge_filter.qs


class ProductListView(ListView):
    model = Product
    context_object_name = "products"
    queryset = Product.objects.filter(is_private=False).order_by("created_at")
    template_name = "product_management/products.html"
    paginate_by = 8

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        return response


# TODO: give a better name to this view, ideally make it a mixin
class BaseProductDetailView:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        product = get_object_or_404(
            Product, slug=self.kwargs.get("product_slug", None)
        )

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


# TODO: take a deeper look at the capability part
class ProductSummaryView(BaseProductDetailView, TemplateView):
    template_name = "product_management/product_summary.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = context["product"]
        challenges = Challenge.objects.filter(
            product=product, status=Challenge.CHALLENGE_STATUS_AVAILABLE
        )
        product_role_assignments = ProductRoleAssignment.objects.filter(
            Q(product=product) & ~Q(role=ProductRoleAssignment.CONTRIBUTOR)
        )
        if self.request.user.is_authenticated:
            context.update(
                {
                    "can_edit_product": product_role_assignments.filter(
                        person=self.request.user.person
                    ).exists()
                }
            )
        else:
            context.update({"can_edit_product": False})
        context.update(
            {
                "product": product,
                "challenges": challenges,
                "capabilities": Capability.objects.filter(product=product),
            }
        )
        return context


class ProductChallengesView(BaseProductDetailView, TemplateView):
    template_name = "product_management/product_challenges.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        product = context["product"]
        challenges = Challenge.objects.filter(product=product)
        custom_order = Case(
            When(status=Challenge.CHALLENGE_STATUS_AVAILABLE, then=Value(0)),
            When(status=Challenge.CHALLENGE_STATUS_CLAIMED, then=Value(1)),
            When(status=Challenge.CHALLENGE_STATUS_IN_REVIEW, then=Value(2)),
            When(status=Challenge.CHALLENGE_STATUS_BLOCKED, then=Value(3)),
            When(status=Challenge.CHALLENGE_STATUS_DONE, then=Value(4)),
        )
        challenges = challenges.annotate(custom_order=custom_order).order_by(
            "custom_order"
        )
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

        context.update({"capabilities": Capability.get_root_nodes()})

        return context


class ProductAreaDetailCreateUpdateView(
    BaseProductDetailView, CreateView, UpdateView, DeleteView
):
    template_name = "product_management/product_area_detail.html"
    model = Capability
    form_class = ProductAreaUpdateForm

    def is_ajax(self):
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            return True
        return False

    def get_success_url(self):
        conttext = self.get_context_data()
        return reverse(
            "product_tree_interactive", args=(conttext.get("product").slug,)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = ProductAreaUpdateForm(instance=self.get_object())
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        if self.is_ajax():
            if form.cleaned_data.get("is_drag"):
                parent_id = form.cleaned_data.get("data_parent_id")
                if parent_id:
                    parent = Capability.objects.get(pk=parent_id)
                    self.object.move(parent, "first-child")
                else:
                    self.object.move(None, "first-sibling")
            else:
                self.object.save()
            return JsonResponse({"success": True})

        else:
            self.object.save()
            return redirect(self.get_success_url())

    def form_invalid(self, form):
        if self.is_ajax():
            return JsonResponse({"errors": form.errors}, status=400)
        return redirect(self.get_success_url())


class ProductTreeInteractiveView(BaseProductDetailView, TemplateView):
    template_name = "product_management/product_tree_interactive.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        capability_root_trees = Capability.get_root_nodes()

        def serialize_tree(node):
            serialized_node = {
                "id": node.pk,
                "name": node.name,
                "description": node.description,
                "video_link": node.video_link,
                "video_name": node.video_name,
                "video_duration": node.video_duration,
                "children": [
                    serialize_tree(child) for child in node.get_children()
                ],
            }
            return serialized_node

        context["tree_data"] = [
            serialize_tree(node) for node in capability_root_trees
        ]

        return context


class ProductIdeasAndBugsView(BaseProductDetailView, TemplateView):
    template_name = "product_management/product_ideas_and_bugs.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = context["product"]

        context.update(
            {
                "ideas": Idea.objects.filter(product=product),
                "bugs": Bug.objects.filter(product=product),
            }
        )

        return context


class ProductIdeaListView(BaseProductDetailView, ListView):
    model = Idea
    template_name = "product_management/product_idea_list.html"
    context_object_name = "ideas"
    object_list = []

    def get_queryset(self):
        context = self.get_context_data()
        product = context.get("product")
        return self.model.objects.filter(product=product)


class ProductBugListView(BaseProductDetailView, ListView):
    model = Bug
    template_name = "product_management/product_bug_list.html"
    context_object_name = "bugs"
    object_list = []

    def get_queryset(self):
        context = self.get_context_data()
        product = context.get("product")
        return self.model.objects.filter(product=product)


# If the user is not authenticated, we redirect him to the sign up page using LoginRequiredMixing.
# After he signs in, we should redirect him with the help of redirect_field_name attribute
# See for more detail: https://docs.djangoproject.com/en/4.2/topics/auth/default/
class CreateProductIdea(LoginRequiredMixin, BaseProductDetailView, CreateView):
    login_url = "sign_in"
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
    login_url = "sign_in"
    template_name = "product_management/update_product_idea.html"
    model = Idea
    form_class = IdeaForm

    def get(
        self, request: HttpRequest, *args: str, **kwargs: Any
    ) -> HttpResponse:
        idea_pk = kwargs.get("pk")
        idea = Idea.objects.get(pk=idea_pk)
        form = IdeaForm(request.GET, instance=idea)

        return super().get(request, *args, **kwargs)

    def post(
        self, request: HttpRequest, *args: str, **kwargs: Any
    ) -> HttpResponse:
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
                "product_people": ProductRoleAssignment.objects.filter(
                    product=product
                ),
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
class ChallengeDetailView(BaseProductDetailView, DetailView):
    model = Challenge
    template_name = "product_management/challenge_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        challenge = self.object
        bounty = challenge.bounty_set.all().first()
        # TODO: we need to allow multiple bounties for a challenge
        bounty_claim = BountyClaim.objects.filter(
            bounty=bounty,
            kind__in=[
                BountyClaim.CLAIM_TYPE_DONE,
                BountyClaim.CLAIM_TYPE_ACTIVE,
            ],
        ).first()

        context.update(
            {
                "challenge": challenge,
                "bounty": bounty,
                "bounty_claim_form": BountyClaimForm(),
                "bounty_claim": bounty_claim,
            }
        )

        if self.request.user.is_authenticated:
            bounty_claims = BountyClaim.objects.filter(
                bounty=bounty,
                person=self.request.user.person,
                kind__in=[
                    BountyClaim.CLAIM_TYPE_ACTIVE,
                    BountyClaim.CLAIM_TYPE_IN_REVIEW,
                ],
            )

            context.update(
                {
                    "current_user_created_claim_request": bounty_claims.count()
                    > 0,
                    "actions_available": challenge.created_by
                    == self.request.user.person,
                }
            )
        else:
            context.update(
                {
                    "current_user_created_claim_request": False,
                    "actions_available": False,
                }
            )

        # todo: fix this ugly if statement
        if (
            bounty_claim
            and bounty_claim.kind
            in [
                BountyClaim.CLAIM_TYPE_ACTIVE,
                BountyClaim.CLAIM_TYPE_DONE,
            ]
            and bounty_claim.bounty.status == Bounty.BOUNTY_STATUS_DONE
            and bounty_claim.bounty.challenge.status
            == Challenge.CHALLENGE_STATUS_DONE
        ):
            context.update(
                {"is_claimed": True, "claimed_by": bounty_claim.person}
            )
        else:
            context.update({"is_claimed": False})

        return context


class CreateInitiativeView(
    LoginRequiredMixin, BaseProductDetailView, CreateView
):
    form_class = InitiativeForm
    template_name = "product_management/create_initiative.html"
    login_url = "sign_in"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["slug"] = self.kwargs.get("product_slug")

        return kwargs

    def get_success_url(self):
        return reverse(
            "product_initiatives",
            args=(self.kwargs.get("product_slug"),),
        )

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)

            product = form.cleaned_data.get("product")
            instance.product = product
            instance.save()

            return HttpResponseRedirect(self.get_success_url())

        return super().post(request, *args, **kwargs)


class InitiativeDetailView(BaseProductDetailView, TemplateView):
    template_name = "product_management/initiative_detail.html"


class CreateCapability(LoginRequiredMixin, BaseProductDetailView, CreateView):
    form_class = CapabilityForm
    template_name = "product_management/create_capability.html"
    login_url = "sign_in"

    # def get_form_kwargs(self):
    #     kwargs = super().get_form_kwargs()
    #     kwargs["slug"] = self.kwargs.get("product_slug", None)

    #     return kwargs

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            name = form.cleaned_data.get("name")
            description = form.cleaned_data.get("description")
            capability = form.cleaned_data.get("root")
            creation_method = form.cleaned_data.get("creation_method")
            product = Product.objects.get(slug=kwargs.get("product_slug"))
            if capability is None or creation_method == "1":
                root = Capability.add_root(name=name, description=description)
                root.product.add(product)
            elif creation_method == "2":
                sibling = capability.add_sibling(
                    name=name, description=description
                )
                sibling.product.add(product)
            elif creation_method == "3":
                sibling = capability.add_child(
                    name=name, description=description
                )
                capability.add_child(sibling)

            return redirect(
                reverse(
                    "product_tree",
                    args=(
                        kwargs.get(
                            "product_slug",
                        ),
                    ),
                )
            )

        return super().post(request, *args, **kwargs)


class CapabilityDetailView(BaseProductDetailView, DetailView):
    model = Capability
    context_object_name = "capability"
    template_name = "product_management/capability_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["challenges"] = Challenge.objects.filter(
            capability=self.object
        )

        return context


class BountyClaimView(LoginRequiredMixin, FormView):
    form_class = BountyClaimForm
    template_name = "product_management/bounty_claim.html"
    login_url = "sign_in"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        pk = self.kwargs.get("pk")
        challenge = get_object_or_404(Challenge, pk=pk)

        context["challenge_pk"] = pk
        context["challenge"] = challenge

        return context

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)

            context = self.get_context_data(**kwargs)
            challenge = context.get("challenge")

            instance.bounty = challenge.bounty_set.all().first()
            instance.person = request.user.person
            instance.kind = BountyClaim.CLAIM_TYPE_IN_REVIEW
            instance.save()

            messages.success(
                request, "Your bounty claim request is successfully sent!"
            )

            self.success_url = reverse(
                "challenge_detail",
                args=(
                    challenge.product.slug,
                    challenge.pk,
                ),
            )
            return redirect(self.success_url)

        return super().post(request, *args, **kwargs)


class CreateProductView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = "product_management/create_product.html"
    login_url = "sign_in"

    def _is_htmx_request(self, request):
        htmx_header = request.headers.get("Hx-Request", None)
        return htmx_header == "true"

    # TODO: save the image and the documents
    def post(self, request, *args, **kwargs):
        if self._is_htmx_request(request):
            return super().post(request, *args, **kwargs)

        # import ipdb

        # ipdb.set_trace()
        form = self.form_class(request.POST, request.FILES, request=request)
        if form.is_valid():
            instance = form.save()
            _ = ProductRoleAssignment.objects.create(
                person=self.request.user.person,
                product=instance,
                role=ProductRoleAssignment.PRODUCT_ADMIN,
            )
            self.success_url = reverse(
                "product_summary", args=(instance.slug,)
            )
            return redirect(self.success_url)

        return super().post(request, *args, **kwargs)


class UpdateProductView(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "product_management/update_product.html"
    login_url = "sign_in"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        # case when owner is the user
        if (
            self.object.content_type_id
            == ContentType.objects.get_for_model(self.request.user.person).id
        ):
            initial_make_me_owner = self.object.object_id == request.user.id
            initial = {"make_me_owner": initial_make_me_owner}

        # case when owner is an organisation
        if (
            self.object.content_type_id
            == ContentType.objects.get_for_model(Organisation).id
        ):
            initial_organisation = Organisation.objects.filter(
                id=self.object.object_id
            ).first()
            initial = {"organisation": initial_organisation}

        form = self.form_class(instance=self.object, initial=initial)
        return render(
            request,
            self.template_name,
            {"form": form, "product_instance": self.object},
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.form_class(
            request.POST, request.FILES, instance=self.object, request=request
        )
        if form.is_valid():
            instance = form.save()
            self.success_url = reverse(
                "product_summary", args=(instance.slug,)
            )
            return redirect(self.success_url)

        return super().post(request, *args, **kwargs)


class CreateOrganisationView(
    LoginRequiredMixin, HTMXInlineFormValidationMixin, CreateView
):
    model = Organisation
    form_class = OrganisationForm
    template_name = "product_management/create_organisation.html"
    success_url = reverse_lazy("create-product")
    login_url = "sign_in"

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
    login_url = "sign_in"

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        product_slug = self.kwargs.get("product_slug", None)
        if product_slug:
            kwargs.update(
                initial={"product": Product.objects.get(slug=product_slug)}
            )

        return kwargs

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.created_by = request.user.person
            instance.save()

            if request.FILES:
                for file in request.FILES.getlist("attachments"):
                    instance.attachment.add(
                        Attachment.objects.create(file=file)
                    )

            messages.success(
                request, _("The challenge is successfully created!")
            )
            self.success_url = reverse(
                "challenge_detail",
                args=(
                    instance.product.slug,
                    instance.id,
                ),
            )
            return redirect(self.success_url)

        return super().post(request, *args, **kwargs)


class UpdateChallengeView(
    LoginRequiredMixin, HTMXInlineFormValidationMixin, UpdateView
):
    model = Challenge
    form_class = ChallengeForm
    template_name = "product_management/update_challenge.html"
    login_url = "sign_in"

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        product_slug = self.kwargs.get("product_slug", None)
        if product_slug:
            kwargs.update(
                initial={"product": Product.objects.get(slug=product_slug)}
            )

        return kwargs

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.form_class(
            request.POST, request.FILES, instance=self.object
        )
        if form.is_valid():
            instance = form.save()
            if request.FILES:
                for file in request.FILES.getlist("attachments"):
                    instance.attachment.add(
                        Attachment.objects.create(file=file)
                    )
            messages.success(
                request, _("The challenge is successfully updated!")
            )

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
    login_url = "sign_in"
    success_url = reverse_lazy("challenges")

    def get(self, request, *args, **kwargs):
        challenge_obj = self.get_object()
        person = request.user.person
        if (
            challenge_obj.can_delete_challenge(person)
            or challenge_obj.created_by == person
        ):
            Challenge.objects.get(pk=challenge_obj.pk).delete()
            messages.success(
                request, _("The challenge is successfully deleted!")
            )
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


class DashboardBaseView(LoginRequiredMixin):
    login_url = "sign_in"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        person = self.request.user.person
        photo_url = person.get_photo_url()
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        person = context.get("person")
        active_bounty_claims = BountyClaim.objects.filter(
            person=person, kind=BountyClaim.CLAIM_TYPE_ACTIVE
        )
        product_roles_queryset = ProductRoleAssignment.objects.filter(
            person=person
        ).exclude(role=ProductRoleAssignment.CONTRIBUTOR)

        product_ids = product_roles_queryset.values_list(
            "product_id", flat=True
        )
        products = Product.objects.filter(id__in=product_ids)
        context.update(
            {
                "active_bounty_claims": active_bounty_claims,
                "products": products,
            }
        )
        return context


class DashboardHomeView(DashboardBaseView, TemplateView):
    template_name = "product_management/dashboard/dashboard_home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        person = context.get("person")
        active_bounty_claims = BountyClaim.objects.filter(
            person=person, kind=BountyClaim.CLAIM_TYPE_ACTIVE
        )
        product_roles_queryset = ProductRoleAssignment.objects.filter(
            person=person
        ).exclude(role=ProductRoleAssignment.CONTRIBUTOR)
        product_ids = product_roles_queryset.values_list(
            "product_id", flat=True
        )
        products = Product.objects.filter(id__in=product_ids)
        context.update(
            {
                "active_bounty_claims": active_bounty_claims,
                "products": products,
            }
        )
        return context


class ManageBountiesView(DashboardBaseView, TemplateView):
    template_name = "product_management/dashboard/my_bounties.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        person = self.request.user.person
        queryset = BountyClaim.objects.filter(
            person=person,
            kind__in=[
                BountyClaim.CLAIM_TYPE_ACTIVE,
                BountyClaim.CLAIM_TYPE_IN_REVIEW,
            ],
        )
        context.update({"bounty_claims": queryset})
        return context


class DashboardBountyClaimRequestsView(LoginRequiredMixin, ListView):
    model = BountyClaim
    context_object_name = "bounty_claims"
    template_name = "product_management/dashboard/bounty_claim_requests.html"
    login_url = "sign_in"

    def get_queryset(self):
        person = self.request.user.person
        queryset = BountyClaim.objects.filter(
            person=person,
            kind__in=[
                BountyClaim.CLAIM_TYPE_ACTIVE,
                BountyClaim.CLAIM_TYPE_IN_REVIEW,
            ],
        )
        return queryset


class DashboardProductDetailView(DashboardBaseView, DetailView):
    model = Product
    template_name = "product_management/dashboard/product_detail.html"

    def get_object(self, queryset=None):
        slug = self.kwargs.get("product_slug")
        return get_object_or_404(self.model, slug=slug)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "challenges": Challenge.objects.filter(
                    product=self.object
                ).order_by("-created_at")
            }
        )
        return context


class DashboardProductChallengesView(LoginRequiredMixin, ListView):
    model = Challenge
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
        queryset = Challenge.objects.filter(
            product__slug=product_slug
        ).order_by("-created_at")
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
            queryset = Challenge.objects.filter(
                title__icontains=query_parameter
            )

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
            bounty__challenge__product=product,
            kind=BountyClaim.CLAIM_TYPE_IN_REVIEW,
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


# TODO: make sure the user can't manipulate the URL to create a bounty
class CreateBountyView(LoginRequiredMixin, CreateView):
    model = Bounty
    form_class = BountyForm
    template_name = "product_management/create_bounty.html"
    login_url = "sign_in"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["challenge_queryset"] = Challenge.objects.filter(
            pk=self.kwargs.get("challenge_id")
        )
        return kwargs

    def post(self, request, *args, **kwargs):
        challenge_queryset = Challenge.objects.filter(
            pk=self.kwargs.get("challenge_id")
        )
        form = self.form_class(
            request.POST, challenge_queryset=challenge_queryset
        )
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
    template_name = "product_management/update_bounty.html"
    login_url = "sign_in"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["challenge_queryset"] = Challenge.objects.filter(
            pk=self.kwargs.get("challenge_id")
        )
        return kwargs

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        challenge_queryset = Challenge.objects.filter(
            pk=self.kwargs.get("challenge_id")
        )
        form = self.form_class(
            request.POST,
            instance=self.object,
            challenge_queryset=challenge_queryset,
        )
        if form.is_valid():
            instance = form.save(commit=False)
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
                args=(
                    self.object.challenge.product.slug,
                    self.object.challenge.id,
                ),
            )
            return redirect(self.success_url)

        return super().post(request, *args, **kwargs)


class DeleteBountyView(LoginRequiredMixin, DeleteView):
    model = Bounty
    login_url = "sign_in"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        Bounty.objects.get(pk=self.object.pk).delete()
        success_url = reverse(
            "challenge_detail",
            args=(kwargs.get("product_slug"), kwargs.get("challenge_id")),
        )
        return redirect(success_url)


class DeleteBountyClaimView(LoginRequiredMixin, DeleteView):
    model = BountyClaim
    login_url = "sign_in"
    success_url = reverse_lazy("dashboard-bounty-requests")

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        instance = BountyClaim.objects.get(pk=self.object.pk)
        if instance.kind == BountyClaim.CLAIM_TYPE_IN_REVIEW:
            instance.delete()
            messages.success(
                request, _("The bounty claim is successfully deleted.")
            )
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
            "dashboard-product-bounties",
            args=(instance.bounty.challenge.product.slug,),
        )
    )


class DashboardReviewWorkView(LoginRequiredMixin, ListView):
    model = BountyDeliveryAttempt
    context_object_name = "bounty_deliveries"
    queryset = BountyDeliveryAttempt.objects.filter(
        kind=BountyDeliveryAttempt.SUBMISSION_TYPE_NEW
    )
    template_name = "product_management/dashboard/review_work.html"
    login_url = "sign_in"


class CreateProductBug(LoginRequiredMixin, BaseProductDetailView, CreateView):
    login_url = "sign_in"
    template_name = "product_management/add_product_bug.html"
    form_class = BugForm

    def post(self, request, *args, **kwargs):
        form = BugForm(request.POST)

        if form.is_valid():
            person = self.request.user.person
            product = Product.objects.get(slug=kwargs.get("product_slug"))

            bug = form.save(commit=False)
            bug.person = person
            bug.product = product
            bug.save()

            return redirect("product_ideas_bugs", **kwargs)

        return super().post(request, *args, **kwargs)


class ProductBugDetail(BaseProductDetailView, DetailView):
    template_name = "product_management/product_bug_detail.html"
    model = Bug
    context_object_name = "bug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(
            {
                "pk": self.object.pk,
            }
        )

        if self.request.user.is_authenticated:
            context.update(
                {
                    "actions_available": self.object.person
                    == self.request.user.person,
                }
            )
        else:
            context.update({"actions_available": False})

        return context


class UpdateProductBug(LoginRequiredMixin, BaseProductDetailView, UpdateView):
    login_url = "sign_in"
    template_name = "product_management/update_product_bug.html"
    model = Bug
    form_class = BugForm

    def get(
        self, request: HttpRequest, *args: str, **kwargs: Any
    ) -> HttpResponse:
        bug_pk = kwargs.get("pk")
        bug = Bug.objects.get(pk=bug_pk)

        if bug.person != self.request.user.person:
            raise PermissionDenied

        return super().get(request, *args, **kwargs)

    def post(
        self, request: HttpRequest, *args: str, **kwargs: Any
    ) -> HttpResponse:
        bug_pk = kwargs.get("pk")
        bug = Bug.objects.get(pk=bug_pk)

        form = BugForm(request.POST, instance=bug)

        if form.is_valid():
            form.save()

            return redirect("product_bug_detail", **kwargs)

        return super().post(request, *args, **kwargs)


class DeleteAttachmentView(LoginRequiredMixin, DeleteView):
    model = Attachment
    template_name = "product_management/delete_attachment.html"
    login_url = "sign_in"

    def get(self, request, *args, **kwargs):
        attachment = self.get_object()
        challenge = Challenge.objects.get(attachment=attachment)
        if request.user.person == challenge.created_by:
            attachment.delete()
            messages.success(
                request, _("The attachment is successfully deleted!")
            )

        return redirect(
            reverse(
                "challenge_detail",
                args=(challenge.product.slug, challenge.id),
            )
        )
