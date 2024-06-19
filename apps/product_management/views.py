import uuid
from typing import Any, Dict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import BadRequest, PermissionDenied
from django.db import models
from django.http import HttpRequest, JsonResponse
from django.shortcuts import HttpResponse, HttpResponseRedirect, get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, RedirectView, TemplateView, UpdateView

from apps.canopy import utils as canopy_utils
from apps.commerce.models import Organisation
from apps.common import mixins as common_mixins
from apps.openunited.mixins import HTMXInlineFormValidationMixin
from apps.product_management import forms, utils
from apps.security.models import ProductRoleAssignment
from apps.talent.forms import PersonSkillFormSet
from apps.talent.models import BountyClaim, BountyDeliveryAttempt, Expertise, Skill
from apps.talent.utils import serialize_skills
from apps.utility import utils as global_utils

from .models import (
    Bounty,
    Bug,
    Challenge,
    Idea,
    IdeaVote,
    Initiative,
    Product,
    ProductArea,
    ProductContributorAgreement,
    ProductContributorAgreementTemplate,
)


class ProductListView(ListView):
    model = Product
    context_object_name = "products"
    queryset = Product.objects.filter(is_private=False).order_by("created_at")
    template_name = "product_management/products.html"
    paginate_by = 8

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["challenge_status"] = Challenge.ChallengeStatus
        return context


class ProductRedirectView(utils.BaseProductDetailView, RedirectView):
    def get(self, request, *args, **kwargs):
        url = reverse("product_summary", kwargs=kwargs)
        return redirect(url)


# TODO: take a deeper look at the capability part
class ProductSummaryView(utils.BaseProductDetailView, TemplateView):
    template_name = "product_management/product_summary.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = context["product"]
        challenges = Challenge.objects.filter(product=product, status=Challenge.ChallengeStatus.ACTIVE)

        can_modify_product = False
        if self.request.user.is_authenticated:
            can_modify_product = utils.has_product_modify_permission(self.request.user, product)

        context["can_modify_product"] = can_modify_product
        context["challenges"] = challenges
        context["tree_data"] = [
            utils.serialize_tree(node) for node in ProductArea.get_root_nodes().filter(product_tree=None)
        ]
        return context


def redirect_challenge_to_bounties(request):
    return redirect(reverse("bounties"))


class BountyListView(ListView):
    model = Bounty
    context_object_name = "bounties"
    paginate_by = 51

    def get_template_names(self):
        if self.request.htmx:
            return ["product_management/bounty/partials/list_partials.html"]
        return ["product_management/bounty/list.html"]

    def get_queryset(self):
        filters = ~models.Q(challenge__status=Challenge.ChallengeStatus.DRAFT)

        if expertise := self.request.GET.get("expertise"):
            filters &= models.Q(expertise=expertise)

        if status := self.request.GET.get("status"):
            filters &= models.Q(status=status)

        if skill := self.request.GET.get("skill"):
            filters &= models.Q(skill=skill)
        return Bounty.objects.filter(filters).select_related("challenge", "skill").prefetch_related("expertise")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["BountyStatus"] = Bounty.BountyStatus

        expertises = []
        if skill := self.request.GET.get("skill"):
            expertises = Expertise.get_roots().filter(skill=skill)

        context["skills"] = [global_utils.serialize_other_type_tree(skill) for skill in Skill.get_roots()]
        context["expertises"] = [global_utils.serialize_other_type_tree(expertise) for expertise in expertises]
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
                {
                    "list_html": list_html,
                    "expertise_html": expertise_html,
                    "item_found_count": context["object_list"].count(),
                }
            )
        return super().render_to_response(context, **response_kwargs)


class ProductBountyListView(utils.BaseProductDetailView, ListView):
    model = Bounty
    context_object_name = "bounties"
    object_list = []

    def get_template_names(self):
        return ["product_management/product_bounties.html"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["request"] = self.request
        return context

    def get_queryset(self):
        context = self.get_context_data()
        product = context.get("product")
        return Bounty.objects.filter(challenge__product=product).exclude(
            challenge__status=Challenge.ChallengeStatus.DRAFT
        )


class ProductChallengesView(utils.BaseProductDetailView, TemplateView):
    template_name = "product_management/product_challenges.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        product = context["product"]
        challenges = Challenge.objects.filter(product=product)
        custom_order = models.Case(
            models.When(status=Challenge.ChallengeStatus.ACTIVE, then=models.Value(0)),
            models.When(status=Challenge.ChallengeStatus.BLOCKED, then=models.Value(1)),
            models.When(status=Challenge.ChallengeStatus.COMPLETED, then=models.Value(2)),
            models.When(status=Challenge.ChallengeStatus.CANCELLED, then=models.Value(3)),
        )
        challenges = challenges.annotate(custom_order=custom_order).order_by("custom_order")
        context["challenges"] = challenges
        context["challenge_status"] = Challenge.ChallengeStatus
        return context


class ProductInitiativesView(utils.BaseProductDetailView, TemplateView):
    template_name = "product_management/product_initiatives.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        initiatives = Initiative.objects.filter(product=context["product"]).annotate(
            total_points=models.Sum(
                "challenge__bounty__points",
                filter=models.Q(challenge__bounty__status=Bounty.BountyStatus.AVAILABLE)
                & models.Q(challenge__bounty__is_active=True),
            )
        )
        context["initiatives"] = initiatives
        return context


class ProductAreaCreateView(utils.BaseProductDetailView, CreateView):
    model = ProductArea
    form_class = forms.ProductAreaForm
    template_name = "product_tree/components/partials/create_node_partial.html"

    def get_template_names(self):
        if self.request.method == "POST":
            return ["product_tree/components/partials/add_node_partial.html"]
        elif not self.request.GET.get("parent_id"):
            return ["product_tree/components/partials/create_root_node_partial.html"]
        else:
            return super().get_template_names()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_modify_product"] = utils.has_product_modify_permission(self.request.user, context["product"])
        if self.request.method == "GET":
            context["id"] = str(uuid.uuid4())[:8]
            context["parent_id"] = self.request.GET.get("parent_id")
        context["depth"] = self.request.GET.get("depth", 0)
        context["product_slug"] = self.kwargs.get("product_slug")
        return context

    def form_valid(self, form, **kwargs):
        context = self.get_context_data(**kwargs)
        try:
            parent = ProductArea.objects.get(pk=self.request.POST.get("parent_id"))
            new_node = parent.add_child(**form.cleaned_data)
        except ProductArea.DoesNotExist:
            new_node = ProductArea.add_root(**form.cleaned_data)

        context["product_area"] = new_node
        context["node"] = [utils.serialize_tree(new_node)]
        context["depth"] = int(self.request.POST.get("depth", 0))
        return render(self.request, self.get_template_names(), context)

    def form_invalid(self, form):
        return super().form_invalid(form)


class ProductAreaUpdateView(utils.BaseProductDetailView, common_mixins.AttachmentMixin, UpdateView):
    template_name = "product_management/product_area_detail.html"
    model = ProductArea
    form_class = forms.ProductAreaForm

    def get_success_url(self):
        product_slug = self.get_context_data()["product"].slug
        return reverse("product_tree", args=(product_slug,))

    def get_template_names(self):
        request = self.request
        if request.htmx:
            return "product_tree/components/partials/update_node_partial.html"
        else:
            return super().get_template_names()

    def get_context_data(self, **kwargs):
        product = Product.objects.get(slug=self.kwargs.get("product_slug"))
        product_perm = utils.has_product_modify_permission(self.request.user, product)
        product_area = ProductArea.objects.get(pk=self.kwargs["pk"])
        challenges = Challenge.objects.filter(product_area=product_area)

        form = forms.ProductAreaForm(instance=product_area, can_modify_product=product_perm)
        context = super().get_context_data(**kwargs)
        new_context = {
            "product": product,
            "product_slug": product.slug,
            "can_modify_product": product_perm,
            "form": form,
            "challenges": challenges,
            "product_area": product_area,
            "margin_left": int(self.request.GET.get("margin_left", 0)) + 4,
            "depth": int(self.request.GET.get("depth", 0)),
        }
        context.update(**new_context)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        if not self.request.htmx:
            return super().form_save(form)
        return canopy_utils.update_node_helper(self.request, context["product_area"])


class ProductAreaDetailView(utils.BaseProductDetailView, common_mixins.AttachmentMixin, DetailView):
    template_name = "product_management/product_area_detail.html"

    model = ProductArea
    context_object_name = "product_area"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["children"] = utils.serialize_tree(self.get_object())["children"]
        return context


class ProductTreeInteractiveView(utils.BaseProductDetailView, TemplateView):
    template_name = "product_management/product_tree.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_modify_product"] = utils.has_product_modify_permission(self.request.user, context["product"])
        capability_root_trees = ProductArea.get_root_nodes().filter(product_tree=None)
        context["tree_data"] = [utils.serialize_tree(node) for node in capability_root_trees]
        return context


class ProductIdeasAndBugsView(utils.BaseProductDetailView, TemplateView):
    template_name = "product_management/product_ideas_and_bugs.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = context["product"]

        ideas_with_votes = []
        user = self.request.user

        if user.is_authenticated:
            for idea in Idea.objects.filter(product=product):
                num_votes = IdeaVote.objects.filter(idea=idea).count()
                user_has_voted = IdeaVote.objects.filter(voter=user, idea=idea).exists()
                ideas_with_votes.append(
                    {
                        "idea_obj": idea,
                        "num_votes": num_votes,
                        "user_has_voted": user_has_voted,
                    }
                )
        else:
            for idea in Idea.objects.filter(product=product):
                ideas_with_votes.append(
                    {
                        "idea_obj": idea,
                    }
                )

        context.update(
            {
                "ideas": ideas_with_votes,
                "bugs": Bug.objects.filter(product=product),
            }
        )

        return context


class ProductIdeaListView(utils.BaseProductDetailView, ListView):
    model = Idea
    template_name = "product_management/product_idea_list.html"
    context_object_name = "ideas"
    object_list = []

    def get_queryset(self):
        context = self.get_context_data()
        product = context.get("product")
        return self.model.objects.filter(product=product)


class ProductBugListView(utils.BaseProductDetailView, ListView):
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
class CreateProductIdea(LoginRequiredMixin, utils.BaseProductDetailView, CreateView):
    login_url = "sign_in"
    template_name = "product_management/add_product_idea.html"
    form_class = forms.IdeaForm

    def post(self, request, *args, **kwargs):
        form = forms.IdeaForm(request.POST)

        if form.is_valid():
            person = self.request.user.person
            product = Product.objects.get(slug=kwargs.get("product_slug"))

            idea = form.save(commit=False)
            idea.person = person
            idea.product = product
            idea.save()

            return redirect("product_ideas_bugs", **kwargs)

        return super().post(request, *args, **kwargs)


class UpdateProductIdea(LoginRequiredMixin, utils.BaseProductDetailView, UpdateView):
    login_url = "sign_in"
    template_name = "product_management/update_product_idea.html"
    model = Idea
    form_class = forms.IdeaForm

    def get(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        idea_pk = kwargs.get("pk")
        idea = Idea.objects.get(pk=idea_pk)
        forms.IdeaForm(request.GET, instance=idea)

        return super().get(request, *args, **kwargs)

    def post(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        idea_pk = kwargs.get("pk")
        idea = Idea.objects.get(pk=idea_pk)

        form = forms.IdeaForm(request.POST, instance=idea)

        if form.is_valid():
            form.save()

            return redirect("product_idea_detail", **kwargs)

        return super().post(request, *args, **kwargs)


class ProductRoleAssignmentView(utils.BaseProductDetailView, TemplateView):
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


class ProductIdeaDetail(utils.BaseProductDetailView, DetailView):
    template_name = "product_management/product_idea_detail.html"
    model = Idea
    context_object_name = "idea"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pk"] = self.object.pk
        return context


class ChallengeDetailView(utils.BaseProductDetailView, common_mixins.AttachmentMixin, DetailView):
    model = Challenge
    context_object_name = "challenge"
    template_name = "product_management/challenge_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["BountyStatus"] = Bounty.BountyStatus
        challenge = self.object
        bounties = challenge.bounty_set.all()
        claim_status = BountyClaim.Status

        extra_data = []
        user = self.request.user
        person = user.person if user.is_authenticated else None

        agreement_template = ProductContributorAgreementTemplate.objects.filter(product=challenge.product)
        if agreement_template.exists():
            agreement_template = agreement_template.first()
        else:
            agreement_template = None

        contributor_agreement_status = False
        if person:
            contributor_agreement_status = person.contributor_agreement.filter(
                agreement_template__product=challenge.product
            ).exists()

        for bounty in bounties:
            data = {
                "bounty": bounty,
                "current_user_created_claim_request": False,
                "actions_available": False,
                "has_claimed": False,
                "claimed_by": bounty.claimed_by,
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
                    role=ProductRoleAssignment.ProductRoles.ADMIN,
                ).exists()

                bounty_claim = bounty.bountyclaim_set.filter(person=person).first()

                if bounty.status == Bounty.BountyStatus.AVAILABLE:
                    data["can_be_claimed"] = not bounty_claim

                if bounty_claim and bounty_claim.status == claim_status.REQUESTED and not bounty.claimed_by:
                    data["created_bounty_claim_request"] = True
                    data["bounty_claim"] = bounty_claim

            else:
                if bounty.status == Bounty.BountyStatus.AVAILABLE:
                    data["can_be_claimed"] = True

            data["show_actions"] = (
                data["can_be_claimed"] or data["can_be_modified"] or data["created_bounty_claim_request"]
            )
            data["status"] = bounty.status
            extra_data.append(data)

        context["bounty_data"] = extra_data
        context["does_have_permission"] = utils.has_product_modify_permission(user, context.get("product"))
        context["agreement_status"] = contributor_agreement_status
        context["agreement_template"] = agreement_template
        return context


class CreateInitiativeView(LoginRequiredMixin, utils.BaseProductDetailView, CreateView):
    form_class = forms.InitiativeForm
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


class InitiativeDetailView(utils.BaseProductDetailView, DetailView):
    template_name = "product_management/initiative_detail.html"
    model = Initiative
    context_object_name = "initiative"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["challenges"] = Challenge.objects.filter(
            initiative=self.object, status=Challenge.ChallengeStatus.ACTIVE
        )
        context["bounty_status"] = Bounty.BountyStatus

        return context


class CreateCapability(LoginRequiredMixin, utils.BaseProductDetailView, CreateView):
    form_class = forms.ProductAreaForm1
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
                sibling = ProductArea.add_sibling(name=name, description=description)
                sibling.product.add(product)
            elif creation_method == "3":
                sibling = capability.add_child(name=name, description=description)
                capability.add_child(sibling)

            return redirect(
                reverse(
                    "product_tree",
                    args=(kwargs.get("product_slug"),),
                )
            )

        return super().post(request, *args, **kwargs)


class CapabilityDetailView(utils.BaseProductDetailView, DetailView):
    model = ProductArea
    context_object_name = "capability"
    template_name = "product_management/capability_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["challenges"] = Challenge.objects.filter(product_area=self.object)

        return context


class BountyClaimView(LoginRequiredMixin, View):
    form_class = forms.BountyClaimForm

    def post(self, request, pk, *args, **kwargs):
        form = forms.BountyClaimForm(request.POST)
        if not form.is_valid():
            return JsonResponse({"errors": form.errors}, status=400)

        instance = form.save(commit=False)
        instance.bounty_id = pk
        instance.person = request.user.person
        instance.status = BountyClaim.Status.REQUESTED
        instance.save()

        contributor_agreement_templates = instance.bounty.challenge.product.contributor_agreement_templates.all()
        if contributor_agreement_templates.exists():
            agreement_template = contributor_agreement_templates.first()
            if not ProductContributorAgreement.objects.filter(
                agreement_template=agreement_template, person=instance.person
            ).exists():
                contributor_agreement = ProductContributorAgreement()
                contributor_agreement.agreement_template = agreement_template
                contributor_agreement.person = instance.person
                contributor_agreement.save()

        return render(
            request,
            "product_management/partials/buttons/delete_bounty_claim_button.html",
            context={"bounty_claim": instance},
        )


class CreateProductView(LoginRequiredMixin, common_mixins.AttachmentMixin, CreateView):
    model = Product
    form_class = forms.ProductForm
    template_name = "product_management/create_product.html"
    login_url = "sign_in"

    def get_success_url(self):
        return reverse("product_summary", args=(self.object.slug,))

    def form_valid(self, form):
        response = super().form_valid(form)
        if not self.request.htmx:
            ProductRoleAssignment.objects.create(
                person=self.request.user.person,
                product=form.instance,
                role=ProductRoleAssignment.ProductRoles.ADMIN,
            )
        return response


class UpdateProductView(LoginRequiredMixin, common_mixins.AttachmentMixin, UpdateView):
    model = Product
    form_class = forms.ProductForm
    template_name = "product_management/update_product.html"
    login_url = "sign_in"

    def get_success_url(self):
        return reverse("product_summary", args=(self.object.slug,))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        initial = {}
        if self.object.content_type_id == ContentType.objects.get_for_model(self.request.user.person).id:
            initial_make_me_owner = self.object.object_id == self.request.user.id
            initial = {"make_me_owner": initial_make_me_owner}
            context["make_me_owner"] = initial_make_me_owner

        if self.object.content_type_id == ContentType.objects.get_for_model(Organisation).id:
            initial_organisation = Organisation.objects.filter(id=self.object.object_id).first()
            initial = {"organisation": initial_organisation}
            context["organisation"] = initial_organisation

        context["form"] = self.form_class(instance=self.object, initial=initial)
        context["product_instance"] = self.object
        return context

    def form_valid(self, form):
        return super().form_save(form)


class CreateOrganisationView(LoginRequiredMixin, HTMXInlineFormValidationMixin, CreateView):
    model = Organisation
    form_class = forms.OrganisationForm
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
    LoginRequiredMixin, common_mixins.AttachmentMixin, HTMXInlineFormValidationMixin, CreateView
):
    model = Challenge
    form_class = forms.ChallengeForm
    template_name = "product_management/create_challenge.html"
    login_url = "sign_in"

    def get_success_url(self):
        return reverse("challenge_detail", args=(self.object.product.slug, self.object.id))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        product_slug = self.kwargs.get("product_slug", None)
        product = Product.objects.get(slug=product_slug)

        context["product"] = product

        context["skills"] = [serialize_skills(skill) for skill in Skill.get_roots()]

        context["form"] = self.form_class(self.request.POST, self.request.FILES)
        context["bounty_form"] = forms.BountyForm()
        context["empty_form"] = PersonSkillFormSet().empty_form

        context["bounty_formset"] = forms.BountyFormset(data={"form-TOTAL_FORMS": "0", "form-INITIAL_FORMS": 0})

        return context

    def form_valid(self, form):
        product_slug = self.kwargs.get("product_slug", None)
        form.instance.product = Product.objects.get(slug=product_slug)
        form.instance.created_by = self.request.user.person
        response = super().form_save(form)

        bounty_formset = forms.BountyFormset(self.request.POST)
        if bounty_formset.is_valid():
            for bounty_form in bounty_formset:
                bounty = bounty_form.save(commit=False)
                bounty.challenge = form.instance

                skill_id = bounty_form.cleaned_data.get("skill")
                bounty.skill = Skill.objects.get(id=skill_id)
                bounty.save()

                expertise_ids = bounty_form.cleaned_data.get("expertise_ids")
                for expertise in Expertise.objects.filter(id__in=expertise_ids.split(",")):
                    bounty.expertise.add(expertise)
                bounty.save()

        return response


class UpdateChallengeView(
    LoginRequiredMixin, common_mixins.AttachmentMixin, HTMXInlineFormValidationMixin, UpdateView
):
    model = Challenge
    form_class = forms.ChallengeForm
    template_name = "product_management/update_challenge.html"
    login_url = "sign_in"

    def get_success_url(self):
        return reverse("challenge_detail", args=(self.object.product.slug, self.object.id))

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["product"] = self.object.product
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user.person
        return super().form_save(form)


class DeleteChallengeView(LoginRequiredMixin, DeleteView):
    model = Challenge
    template_name = "product_management/delete_challenge.html"
    login_url = "sign_in"
    success_url = reverse_lazy("challenges")

    def get(self, request, *args, **kwargs):
        challenge_obj = self.get_object()
        person = request.user.person
        if challenge_obj.can_delete_challenge(person) or challenge_obj.created_by == person:
            Challenge.objects.get(pk=challenge_obj.pk).delete()
            messages.success(request, "The challenge is successfully deleted!")
            return redirect(self.success_url)
        else:
            messages.error(request, "You do not have rights to remove this challenge.")

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
        product_queryset = Product.objects.filter(content_type__model="person", object_id=person.id)
        context.update({"person": person, "photo_url": photo_url, "products": product_queryset})
        return context


class DashboardView(DashboardBaseView, TemplateView):
    template_name = "product_management/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        person = context.get("person")
        active_bounty_claims = BountyClaim.objects.filter(person=person, status=BountyClaim.Status.GRANTED)
        product_roles_queryset = ProductRoleAssignment.objects.filter(person=person).exclude(
            role=ProductRoleAssignment.ProductRoles.CONTRIBUTOR
        )

        product_ids = product_roles_queryset.values_list("product_id", flat=True)
        products = Product.objects.filter(id__in=product_ids)
        context.update({"active_bounty_claims": active_bounty_claims, "products": products})
        return context


class DashboardHomeView(DashboardBaseView, TemplateView):
    template_name = "product_management/dashboard/dashboard_home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        person = context.get("person")
        active_bounty_claims = BountyClaim.objects.filter(person=person, status=BountyClaim.Status.GRANTED)
        product_roles_queryset = ProductRoleAssignment.objects.filter(person=person).exclude(
            role=ProductRoleAssignment.ProductRoles.CONTRIBUTOR
        )
        product_ids = product_roles_queryset.values_list("product_id", flat=True)
        products = Product.objects.filter(id__in=product_ids)
        context.update({"active_bounty_claims": active_bounty_claims, "products": products})
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


class ManageUsersView(DashboardBaseView, TemplateView):
    template_name = "product_management/dashboard/manage_users.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs.get("product_slug")
        product = Product.objects.get(slug=slug)

        product_users = ProductRoleAssignment.objects.filter(product=product).order_by("-role")

        context["product"] = product
        context["product_users"] = product_users

        return context


class AddProductUserView(DashboardBaseView, common_mixins.PersonSearchMixin, CreateView):
    model = ProductRoleAssignment
    form_class = forms.ProductRoleAssignmentForm
    template_name = "product_management/dashboard/add_product_user.html"
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

        product_users = ProductRoleAssignment.objects.filter(product=product).order_by("-role")

        context["product"] = product
        context["product_users"] = product_users

        return context

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            product = Product.objects.get(slug=kwargs.get("product_slug"))

            instance = form.save(commit=False)
            instance.product = product
            instance.save()

            messages.success(request, "The user was successfully added!")

            self.success_url = reverse("manage-users", args=(product.slug,))
            return redirect(self.success_url)

        return super().post(request, *args, **kwargs)


class UpdateProductUserView(DashboardBaseView, common_mixins.PersonSearchMixin, UpdateView):
    model = ProductRoleAssignment
    form_class = forms.ProductRoleAssignmentForm
    template_name = "product_management/dashboard/update_product_user.html"
    login_url = "sign_in"
    context_object_name = "product_role_assignment"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context["search_result"]:
            return context

        slug = self.kwargs.get("product_slug")
        product = Product.objects.get(slug=slug)
        product_users = ProductRoleAssignment.objects.filter(product=product).order_by("-role")

        context["product"] = product
        context["product_users"] = product_users

        return context

    def post(self, request, *args, **kwargs):
        product_role_assignment = ProductRoleAssignment.objects.get(pk=kwargs.get("pk"))
        product = Product.objects.get(slug=kwargs.get("product_slug"))

        form = forms.ProductRoleAssignmentForm(request.POST, instance=product_role_assignment)

        if form.is_valid():
            form.save()

            self.success_url = reverse("manage-users", args=(product.slug,))

            return redirect(self.success_url)

        return super().post(request, *args, **kwargs)


class DashboardBountyClaimRequestsView(LoginRequiredMixin, ListView):
    model = BountyClaim
    context_object_name = "bounty_claims"
    template_name = "product_management/dashboard/bounty_claim_requests.html"
    login_url = "sign_in"

    def get_queryset(self):
        person = self.request.user.person
        return BountyClaim.objects.filter(
            person=person,
            status__in=[BountyClaim.Status.GRANTED, BountyClaim.Status.REQUESTED],
        )


class DashboardProductDetailView(DashboardBaseView, DetailView):
    model = Product
    template_name = "product_management/dashboard/product_detail.html"

    def get_object(self, queryset=None):
        slug = self.kwargs.get("product_slug")
        return get_object_or_404(self.model, slug=slug)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"challenges": Challenge.objects.filter(product=self.object).order_by("-created_at")})
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
        return Challenge.objects.filter(product__slug=product_slug).order_by("-created_at")


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

        if query_parameter := request.GET.get("q"):
            for q in query_parameter.split(" "):
                q = q.split(":")
                key = q[0]
                if key == "sort":
                    value = q[1]

                    if value == "created-asc":
                        queryset = queryset.order_by("created_at")
                    elif value == "created-desc":
                        queryset = queryset.order_by("-created_at")

        if query_parameter := request.GET.get("search-challenge"):
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
        return BountyClaim.objects.filter(
            bounty__challenge__product=product,
            status=BountyClaim.Status.REQUESTED,
        )


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
            queryset = Bounty.objects.filter(challenge__title__icontains=query_parameter)

        context.update({"bounties": queryset})

        return render(request, self.template_name, context)


class BountyDetailView(common_mixins.AttachmentMixin, DetailView):
    model = Bounty
    template_name = "product_management/bounty_detail.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        data = super().get_context_data(**kwargs)

        bounty = data.get("bounty")
        challenge = bounty.challenge
        product = challenge.product
        user = self.request.user

        can_be_modified = False
        can_be_claimed = False
        created_bounty_claim_request = False
        bounty_claim = None
        if user.is_authenticated:
            person = user.person
            _bounty_claim = bounty.bountyclaim_set.filter(person=person).first()

            if _bounty_claim and _bounty_claim.status == BountyClaim.Status.REQUESTED and not bounty.claimed_by:
                created_bounty_claim_request = True
                bounty_claim = _bounty_claim

            if bounty.status == Bounty.BountyStatus.AVAILABLE:
                can_be_claimed = not _bounty_claim

            can_be_modified = ProductRoleAssignment.objects.filter(
                person=person,
                product=product,
                role=ProductRoleAssignment.ProductRoles.ADMIN,
            ).exists()

        data.update(
            {
                "product": product,
                "challenge": challenge,
                "claimed_by": bounty.claimed_by,
                "bounty_claim": bounty_claim,
                "show_actions": created_bounty_claim_request or can_be_claimed or can_be_modified,
                "can_be_claimed": can_be_claimed,
                "can_be_modified": can_be_modified,
                "is_product_admin": True,
                "created_bounty_claim_request": created_bounty_claim_request,
            }
        )

        return {"data": data, "attachment_formset": data["attachment_formset"]}


class CreateBountyView(LoginRequiredMixin, utils.BaseProductDetailView, common_mixins.AttachmentMixin, CreateView):
    model = Bounty
    form_class = forms.BountyForm
    template_name = "product_management/create_bounty.html"
    login_url = "sign_in"

    def get_success_url(self):
        challenge = self.object.challenge
        return reverse("challenge_detail", args=(challenge.product.slug, challenge.pk))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["challenge"] = Challenge.objects.get(pk=self.kwargs.get("challenge_id"))
        context["challenge_queryset"] = Challenge.objects.filter(pk=self.kwargs.get("challenge_id"))
        context["skills"] = [serialize_skills(skill) for skill in Skill.get_roots()]
        context["empty_form"] = PersonSkillFormSet().empty_form
        return context

    def form_valid(self, form):
        form.instance.challenge = Challenge.objects.get(pk=self.kwargs.get("challenge_id"))
        form.instance.skill = Skill.objects.get(id=form.cleaned_data.get("skill"))
        response = super().form_save(form)
        form.instance.expertise.add(
            *Expertise.objects.filter(id__in=form.cleaned_data.get("expertise_ids").split(","))
        )
        form.instance.save()
        return response


class UpdateBountyView(LoginRequiredMixin, utils.BaseProductDetailView, common_mixins.AttachmentMixin, UpdateView):
    model = Bounty
    form_class = forms.BountyForm
    template_name = "product_management/update_bounty.html"
    login_url = "sign_in"

    def get_success_url(self):
        challenge = self.object.challenge
        return reverse("challenge_detail", args=(challenge.product.slug, challenge.pk))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["challenge"] = Challenge.objects.get(pk=self.kwargs.get("challenge_id"))
        context["skills"] = [serialize_skills(skill) for skill in Skill.get_roots()]
        context["empty_form"] = PersonSkillFormSet().empty_form

        return context

    def form_valid(self, form):
        form.instance.challenge = form.cleaned_data.get("challenge")
        form.instance.skill = Skill.objects.get(id=form.cleaned_data.get("skill_id"))
        response = super().form_save(form)
        form.instance.expertise.add(*Expertise.objects.filter(id__in=form.cleaned_data.get("expertise_ids")))
        form.instance.save()
        return response


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

    return redirect(reverse("dashboard-product-bounties", args=(instance.bounty.challenge.product.slug,)))


class DashboardReviewWorkView(LoginRequiredMixin, ListView):
    model = BountyDeliveryAttempt
    context_object_name = "bounty_deliveries"
    queryset = BountyDeliveryAttempt.objects.filter(kind=BountyDeliveryAttempt.SubmissionType.NEW)
    template_name = "product_management/dashboard/review_work.html"
    login_url = "sign_in"


class DashboardContributorAgreementTemplateListView(LoginRequiredMixin, ListView):
    model = ProductContributorAgreementTemplate
    context_object_name = "contributor_agreement_templates"
    login_url = "sign_in"
    template_name = "product_management/dashboard/contributor_agreement_templates.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs.get("product_slug")
        context.update({"product": Product.objects.get(slug=slug)})
        return context

    def get_queryset(self):
        product_slug = self.kwargs.get("product_slug")
        return ProductContributorAgreementTemplate.objects.filter(product__slug=product_slug).order_by("-created_at")


class CreateContributorAgreementTemplateView(LoginRequiredMixin, HTMXInlineFormValidationMixin, CreateView):
    model = ProductContributorAgreementTemplate
    form_class = forms.ContributorAgreementTemplateForm
    template_name = "product_management/create_contributor_agreement_template.html"
    login_url = "sign_in"

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        if product_slug := self.kwargs.get("product_slug", None):
            kwargs.update(initial={"product": Product.objects.get(slug=product_slug)})

        return kwargs

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            instance = form.save(commit=False)
            instance.created_by = request.user.person
            instance.save()

            messages.success(request, "The contribution agreement is successfully created!")

            self.success_url = reverse(
                "contributor-agreement-template-detail",
                args=(
                    instance.product.slug,
                    instance.id,
                ),
            )
            return redirect(self.success_url)

        return super().post(request, *args, **kwargs)


class ContributorAgreementTemplateView(DetailView):
    model = ProductContributorAgreementTemplate
    template_name = "product_management/contributor_agreement_template_detail.html"
    context_object_name = "contributor_agreement_template"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs.get("product_slug")
        context.update(
            {
                "product": Product.objects.get(slug=slug),
                "pk": self.object.pk,
            }
        )
        return context


class CreateProductBug(LoginRequiredMixin, utils.BaseProductDetailView, CreateView):
    login_url = "sign_in"
    template_name = "product_management/add_product_bug.html"
    form_class = forms.BugForm

    def post(self, request, *args, **kwargs):
        form = forms.BugForm(request.POST)

        if form.is_valid():
            person = self.request.user.person
            product = Product.objects.get(slug=kwargs.get("product_slug"))

            bug = form.save(commit=False)
            bug.person = person
            bug.product = product
            bug.save()

            return redirect("product_ideas_bugs", **kwargs)

        return super().post(request, *args, **kwargs)


class ProductBugDetail(utils.BaseProductDetailView, DetailView):
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
                    "actions_available": self.object.person == self.request.user.person,
                }
            )
        else:
            context.update({"actions_available": False})

        return context


class UpdateProductBug(LoginRequiredMixin, utils.BaseProductDetailView, UpdateView):
    login_url = "sign_in"
    template_name = "product_management/update_product_bug.html"
    model = Bug
    form_class = forms.BugForm

    def get(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        bug_pk = kwargs.get("pk")
        bug = Bug.objects.get(pk=bug_pk)

        if bug.person != self.request.user.person:
            raise PermissionDenied

        return super().get(request, *args, **kwargs)

    def post(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        bug_pk = kwargs.get("pk")
        bug = Bug.objects.get(pk=bug_pk)

        form = forms.BugForm(request.POST, instance=bug)

        if form.is_valid():
            form.save()

            return redirect("product_bug_detail", **kwargs)

        return super().post(request, *args, **kwargs)


@login_required(login_url="sign_in")
def cast_vote_for_idea(request, pk):
    idea = Idea.objects.get(pk=pk)
    if IdeaVote.objects.filter(idea=idea, voter=request.user).exists():
        IdeaVote.objects.get(idea=idea, voter=request.user).delete()
    else:
        IdeaVote.objects.create(idea=idea, voter=request.user)

    return HttpResponse(IdeaVote.objects.filter(idea=idea).count())
