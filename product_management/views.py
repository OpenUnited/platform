from typing import Any, Dict
from django.forms import BaseModelForm
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
from django.views import View
from django.views.generic import (
    ListView,
    TemplateView,
    RedirectView,
    CreateView,
    UpdateView,
    DeleteView,
    DetailView,
)
from django.views import View

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
    ProductAreaForm,
    ProductAreaAttachmentSet,
    BountyAttachmentFormSet,
)
from talent.models import BountyClaim, BountyDeliveryAttempt
from .models import (
    Challenge,
    Product,
    Initiative,
    Bounty,
    ProductArea,
    Idea,
    Bug,
    Skill,
    Expertise,
    Attachment,
    BountyAttachment,
)
from commerce.models import Organisation
from security.models import ProductRoleAssignment
from openunited.mixins import HTMXInlineFormValidationMixin
from django.http import JsonResponse

from .filters import ChallengeFilter
from product_management import utils
import uuid


class ChallengeListView(ListView):
    model = Challenge
    context_object_name = "challenges"
    template_name = "product_management/challenges.html"
    paginate_by = 8
    filterset_class = ChallengeFilter

    def get_template_names(self):
        if self.request.htmx:
            return [
                "product_management/partials/challenge_filter_partial.html"
            ]
        return super().get_template_names()

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
        context["product"] = product
        context["product_slug"] = product.slug
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
            context["can_modify_product"] = product_role_assignments.filter(
                person=self.request.user.person
            ).exists()

        else:
            context["can_modify_product"] = False

        context["challenges"] = challenges
        context["tree_data"] = [
            utils.serialize_tree(node) for node in ProductArea.get_root_nodes()
        ]
        return context


class BountyListView(ListView):
    model = Bounty
    context_object_name = "bounties"
    paginate_by = 50

    def get_template_names(self):
        if self.request.htmx:
            return ["product_management/bounty/partials/list_partials.html"]
        return ["product_management/bounty/list.html"]

    def get_queryset(self):
        queryset = super().get_queryset()
        filters = Q()

        if expertise := self.request.GET.get("expertise"):
            filters &= Q(expertise=expertise)

        if status := self.request.GET.get("status"):
            filters &= Q(status=status)

        if skill := self.request.GET.get("skill"):
            filters &= Q(skill=skill)

        return queryset.filter(filters)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["request"] = self.request

        expertises = []
        if skill := self.request.GET.get("skill"):
            expertises = Expertise.get_roots().filter(skill=skill)

        context["skills"] = [
            utils.serialize_other_type_tree(skill)
            for skill in Skill.get_roots()
        ]
        context["expertises"] = [
            utils.serialize_other_type_tree(expertise)
            for expertise in expertises
        ]
        context["statuses"] = [
            status for status in Bounty.BOUNTY_STATUS if status[0] != 0
        ]

        return context

    def render_to_response(self, context, **response_kwargs):
        from django.template.loader import render_to_string

        if self.request.htmx and self.request.GET.get("target") == "skill":
            list_html = render_to_string(
                "product_management/bounty/partials/list_partials.html",
                context,
                request=self.request,
            )
            expertise_html = render_to_string(
                "product_management/bounty/partials/expertise.html",
                context,
                request=self.request,
            )
            return JsonResponse(
                {"list_html": list_html, "expertise_html": expertise_html}
            )
        return super().render_to_response(context, **response_kwargs)


class ProductBountyListView(BaseProductDetailView, ListView):
    model = Bounty
    context_object_name = "bounties"
    paginate_by = 50

    def get_template_names(self):
        return ["product_management/bounty/product_bounties.html"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["request"] = self.request
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

        context.update({"capabilities": ProductArea.get_root_nodes()})

        return context


class ProductAreaCreateView(BaseProductDetailView, CreateView):
    model = ProductArea
    form_class = ProductAreaForm
    template_name = "product_management/tree_helper/create_node_partial.html"

    def get_template_names(self):
        if self.request.method == "POST":
            return ["product_management/tree_helper/add_node_partial.html"]
        return super().get_template_names()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_modify_product"] = utils.has_product_modify_permission(
            self.request.user, context["product"]
        )
        return context

    # @utils.modify_permission_required
    def post(self, request, **kwargs):
        form = ProductAreaForm(request.POST)
        if not form.is_valid():
            return render(request, self.get_template_names(), form.errors)
        context = {
            "product_slug": kwargs.get("product_slug"),
        }
        return self.valid_form(request, form, context)

    def valid_form(self, request, form, context):
        if request.POST.get("parent_id") == "None":
            new_node = ProductArea.add_root(**form.cleaned_data)
        else:
            parent_id = request.POST.get("parent_id")
            parent = ProductArea.objects.get(pk=parent_id)
            context["parent_id"] = parent_id
            new_node = parent.add_child(**form.cleaned_data)
        context["product_area"] = new_node
        context["node"] = new_node
        context["depth"] = int(request.POST.get("depth", 0))
        return render(request, self.get_template_names(), context)

    def get(self, request, *args, **kwargs):
        product_area = ProductArea.objects.first()
        if request.GET.get("parent_id"):
            margin_left = int(request.GET.get("margin_left", 0)) + 4
        else:
            margin_left = request.GET.get("margin_left", 0)

        context = {
            "id": str(uuid.uuid4())[:8],
            "product_area": product_area,
            "parent_id": request.GET.get("parent_id"),
            "margin_left": margin_left,
            "depth": request.GET.get("depth", 0),
            "product_slug": kwargs.get("product_slug"),
        }
        return render(request, self.get_template_names(), context)


class ProductAreaDetailUpdateView(BaseProductDetailView, UpdateView):
    template_name = "product_management/product_area_detail.html"
    model = ProductArea
    form_class = ProductAreaForm

    def get_success_url(self):
        product_slug = self.get_context_data()["product"].slug
        product_area = self.get_object()
        return reverse(
            "product_area_update", args=(product_slug, product_area.pk)
        )

    def get_context_data(self, **kwargs):
        product = Product.objects.get(slug=self.kwargs.get("product_slug"))
        product_perm = utils.has_product_modify_permission(
            self.request.user, product
        )
        product_area = ProductArea.objects.get(pk=self.kwargs["pk"])

        attachment_formset = ProductAreaAttachmentSet(
            self.request.POST or None,
            self.request.FILES or None,
            instance=product_area,
        )
        challenges = Challenge.objects.filter(capability=product_area)

        form = ProductAreaForm(
            instance=product_area, can_modify_product=product_perm
        )
        return {
            "product": product,
            "product_slug": product.slug,
            "can_modify_product": product_perm,
            "form": form,
            "attachment_formset": attachment_formset,
            "challenges": challenges,
            "product_area": product_area,
        }

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        context["margin_left"] = int(request.GET.get("margin_left", 0)) + 4
        context["depth"] = int(request.GET.get("depth", 0))

        if request.htmx and request.GET.get("is_attachment", False):
            template_name = (
                "product_management/product_area_detail_helper/empty_form.html"
            )
        elif request.htmx:
            template_name = (
                "product_management/tree_helper/update_node_partial.html"
            )
        else:
            template_name = "product_management/product_area_detail.html"

        return render(request, template_name, context)

    def form_valid(self, form):
        request = self.request
        context = self.get_context_data()
        product_area = context["product_area"]
        product = context["product"]

        has_cancelled = bool(request.POST.get("cancelled", False))
        has_dropped = bool(request.POST.get("has_dropped", False))
        parent_id = request.POST.get("parent_id")

        if request.htmx:
            if not has_cancelled and has_dropped and parent_id:
                parent = ProductArea.objects.get(pk=parent_id)
                product_area.move(parent, "last-child")
                return JsonResponse({})

            if not has_cancelled and form.is_valid():
                product_area.name = form.cleaned_data["name"]
                product_area.description = form.cleaned_data["description"]
                product_area.save()

            context["parent_id"] = int(request.POST.get("parent_id", 0))
            context["depth"] = int(request.POST.get("depth", 0))
            context["descendants"] = utils.serialize_tree(product_area)[
                "children"
            ]
            context["product"] = product
            template_name = (
                "product_management/tree_helper/add_node_partial.html"
            )
            return render(request, template_name, context)
        else:
            attachment_formset = context["attachment_formset"]
            if form.is_valid() and attachment_formset.is_valid():
                obj = form.save()
                attachment_formset.instance = obj
                attachment_formset.save()

            return super().form_valid(form)


class ProductAreaDetailDeleteView(View):
    def delete(self, request, *args, **kwargs):
        product_area = ProductArea.objects.get(pk=kwargs.get("pk"))
        if product_area.numchild > 0:
            return JsonResponse(
                {"error": "Unable to delete a node with a child."}, status=400
            )

        product_area.delete()
        return JsonResponse(
            {"message": "The node has been deleted successfully"}, status=204
        )


class ProductTreeInteractiveView(BaseProductDetailView, TemplateView):
    template_name = "product_management/product_tree.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_modify_product"] = utils.has_product_modify_permission(
            self.request.user, context["product"]
        )
        capability_root_trees = ProductArea.get_root_nodes()
        context["tree_data"] = [
            utils.serialize_tree(node) for node in capability_root_trees
        ]

        return context


def update_node(request, pk):
    product_area = ProductArea.objects.get(pk=pk)
    context = {
        "product_area": product_area,
        "product_slug": product_area.slug,
        "node": product_area,
    }
    if request.method == "POST":
        form = ProductAreaForm(request.POST)
        has_cancelled = bool(request.POST.get("cancelled", False))
        has_dropped = bool(request.POST.get("has_dropped", False))

        parent_id = request.POST.get("parent_id")
        if not has_cancelled and has_dropped and parent_id:
            parent = ProductArea.objects.get(pk=parent_id)
            product_area.move(parent, "last-child")
            return JsonResponse({})

        if not has_cancelled and form.is_valid():
            product_area.name = form.cleaned_data["name"]
            product_area.description = form.cleaned_data["description"]
            product_area.save()

        context["parent_id"] = int(request.POST.get("parent_id", 0))
        context["depth"] = int(request.POST.get("depth", 0))
        context["descendants"] = utils.serialize_tree(product_area)["children"]
        context["product"] = Product.objects.first()
        template_name = "product_management/tree_helper/add_node_partial.html"

    elif request.method == "GET":
        context["margin_left"] = int(request.GET.get("margin_left", 0)) + 4
        context["depth"] = int(request.GET.get("depth", 0))
        template_name = (
            "product_management/tree_helper/update_node_partial.html"
        )

    elif request.method == "DELETE":
        if product_area.numchild > 0:
            return JsonResponse(
                {"error": "Unable to delete a node with a child."}, status=400
            )
        ProductArea.objects.filter(pk=pk).delete()
        return JsonResponse(
            {"message:": "The node has deleted successfully"}, status=204
        )

    return render(request, template_name, context)


def add_tree_node(request, pk):
    template_name = "product_management/tree_helper/partial_update_node.html"
    product_area = ProductArea.objects.get(pk=pk)

    context = {
        "product_area": product_area,
    }
    return render(request, template_name, context)


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
        context["pk"] = self.object.pk
        return context


class ChallengeDetailView(BaseProductDetailView, DetailView):
    model = Challenge
    context_object_name = "challenge"
    template_name = "product_management/challenge_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        challenge = self.object
        bounties = challenge.bounty_set.all()
        claim_status = BountyClaim.Status

        extra_data = []
        user = self.request.user
        person = user.person if user.is_authenticated else None

        for bounty in bounties:
            data = {
                "bounty": bounty,
                "current_user_created_claim_request": False,
                "actions_available": False,
                "has_claimed": False,
                "claimed_by": None,
                "show_actions": False,
                "can_be_claimed": False,
                "can_be_modified": False,
                "is_product_admin": False,
                "created_bounty_claim_request": False,
                "bounty_claim": None,
            }

            if person:
                data["can_be_modified"] = ProductRoleAssignment.objects.filter(
                    person=person,
                    product=context["product"],
                    role=ProductRoleAssignment.PRODUCT_ADMIN,
                ).exists()

                bounty_claim = bounty.bountyclaim_set.filter(
                    person=person
                ).first()
                last_claim = bounty.bountyclaim_set.filter(
                    status__in=[
                        claim_status.GRANTED,
                        claim_status.COMPLETED,
                        claim_status.CONTRIBUTED,
                    ]
                ).first()

                if bounty.status == Bounty.BOUNTY_STATUS_AVAILABLE:
                    data["can_be_claimed"] = not bounty_claim

                if (
                    bounty_claim
                    and bounty_claim.status == claim_status.REQUESTED
                    and not last_claim
                ):
                    data["created_bounty_claim_request"] = True
                    data["bounty_claim"] = bounty_claim

                if last_claim:
                    data["claimed_by"] = last_claim.person

            else:
                data["can_be_claimed"] = True

            data["show_actions"] = (
                data["can_be_claimed"]
                or data["can_be_modified"]
                or data["created_bounty_claim_request"]
            )
            data["status"] = Bounty.BOUNTY_STATUS[bounty.status][1]
            extra_data.append(data)

        context["bounty_data"] = extra_data
        context["does_have_permission"] = utils.has_product_modify_permission(
            user, context.get("product")
        )
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


class InitiativeDetailView(BaseProductDetailView, DetailView):
    template_name = "product_management/initiative_detail.html"
    model = Initiative
    context_object_name = "initiative"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        initiative = self.object
        return context

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
                root = ProductArea.add_root(name=name, description=description)
                root.product.add(product)
            elif creation_method == "2":
                sibling = ProductArea.add_sibling(
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
    model = ProductArea
    context_object_name = "capability"
    template_name = "product_management/capability_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["challenges"] = Challenge.objects.filter(
            capability=self.object
        )

        return context


class BountyClaimView(LoginRequiredMixin, View):
    form_class = BountyClaimForm

    def post(self, request, pk, *args, **kwargs):
        form = BountyClaimForm(request.POST)
        if not form.is_valid():
            return JsonResponse({"errors": form.errors}, status=400)

        instance = form.save(commit=False)
        instance.bounty_id = pk
        instance.person = request.user.person
        instance.status = BountyClaim.Status.REQUESTED
        instance.save()

        bounty = instance.bounty
        bounty.status = Bounty.BOUNTY_STATUS_AVAILABLE
        bounty.save()

        return render(
            request,
            "product_management/partials/buttons/delete_bounty_claim_button.html",
            context={"bounty_claim": instance},
        )


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
            person=person, status=BountyClaim.Status.GRANTED
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
            person=person, status=BountyClaim.Status.GRANTED
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
            status__in=[
                BountyClaim.Status.GRANTED,
                BountyClaim.Status.REQUESTED,
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
            status__in=[
                BountyClaim.Status.GRANTED,
                BountyClaim.Status.REQUESTED,
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
            status=BountyClaim.Status.REQUESTED,
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


class BountyDetailView(DetailView):
    model = Bounty
    template_name = "product_management/bounty_detail.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        data = super().get_context_data(**kwargs)

        bounty = data.get("bounty")
        challenge = bounty.challenge
        product = challenge.product

        bounty_claims = BountyClaim.objects.filter(
            bounty=bounty,
            status__in=[
                BountyClaim.Status.GRANTED,
                BountyClaim.Status.CONTRIBUTED,
                BountyClaim.Status.COMPLETED,
            ],
        )

        is_assigned = bounty_claims.exists()
        assigned_to = (
            bounty_claims.first().person if bounty_claims else "No one"
        )
        attachments = [
            att for att in BountyAttachment.objects.filter(bounty=bounty)
        ]

        data.update(
            {
                "product": product,
                "challenge": challenge,
                "is_assigned": is_assigned,
                "assigned_to": assigned_to,
                "attachments": attachments,
            }
        )
        return data


# TODO: make sure the user can't manipulate the URL to create a bounty
class CreateBountyView(LoginRequiredMixin, BaseProductDetailView, CreateView):
    model = Bounty
    form_class = BountyForm
    template_name = "product_management/create_bounty.html"
    login_url = "sign_in"

    def get_template_names(self):
        if self.request.htmx:
            return "product_management/forms/bounty_empty_attachment.html"

        return super().get_template_names()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["bounty_attachment_formset"] = BountyAttachmentFormSet(
            self.request.POST or None,
            self.request.FILES or None,
        )
        context["challenge"] = Challenge.objects.get(
            pk=self.kwargs.get("challenge_id")
        )

        return context

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

            self.object = instance
            context = self.get_context_data()
            attachment_formset = context["bounty_attachment_formset"]
            if attachment_formset.is_valid():
                attachment_formset.instance = instance
                attachment_formset.save()

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


class UpdateBountyView(LoginRequiredMixin, BaseProductDetailView, UpdateView):
    model = Bounty
    form_class = BountyForm
    template_name = "product_management/update_bounty.html"
    login_url = "sign_in"

    def get_template_names(self):
        if self.request.htmx:
            return "product_management/forms/bounty_empty_attachment.html"
        return super().get_template_names()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["bounty_attachment_formset"] = BountyAttachmentFormSet(
            self.request.POST or None,
            self.request.FILES or None,
            instance=self.get_object(),
        )
        return context

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
            return self.handle_update(request, form)

        return super().post(request, *args, **kwargs)

    def handle_update(self, request, form):
        context = self.get_context_data()
        instance = form.save(commit=False)
        skill_id = form.cleaned_data.get("selected_skill_ids")[0]
        instance.skill = Skill.objects.get(id=skill_id)
        instance.save()

        attachment_formset = context["bounty_attachment_formset"]
        if attachment_formset.is_valid():
            attachment_formset.instance = instance
            attachment_formset.save()

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
        if instance.status == BountyClaim.Status.REQUESTED:
            instance.status = BountyClaim.Status.CANCELLED
            instance.save()
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

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        instance = BountyClaim.objects.get(pk=self.object.pk)
        if instance.status == BountyClaim.Status.REQUESTED:
            instance.status = BountyClaim.Status.CANCELLED
            instance.save()

        context = self.get_context_data()
        context["bounty"] = self.object.bounty
        template_name = self.request.POST.get("from")
        if template_name == "bounty_detail_table.html":
            return render(
                request,
                "product_management/partials/buttons/create_bounty_claim_button.html",
                context,
            )

        return super().post(request, *args, **kwargs)


def bounty_claim_actions(request, pk):
    instance = BountyClaim.objects.get(pk=pk)
    action_type = request.GET.get("action")
    if action_type == "accept":
        instance.status = BountyClaim.Status.GRANTED

        # If one claim is accepted for a particular challenge, the other claims automatically fails.
        challenge = instance.bounty.challenge
        _ = BountyClaim.objects.filter(bounty__challenge=challenge).update(
            status=BountyClaim.Status.REJECTED
        )
    elif action_type == "reject":
        instance.status = BountyClaim.Status.REJECTED
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
