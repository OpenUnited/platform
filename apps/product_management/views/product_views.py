import uuid
from typing import Any, Dict

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import BadRequest
from django.db import models
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    RedirectView,
    TemplateView,
    UpdateView,
)

from apps.canopy import utils as canopy_utils
from apps.common import mixins as common_mixins
from apps.openunited.mixins import HTMXInlineFormValidationMixin
from apps.product_management import forms, utils
from apps.security.models import ProductRoleAssignment
from apps.talent.forms import PersonSkillFormSet
from apps.talent.models import BountyClaim, Expertise, Skill
from apps.talent.utils import serialize_skills
from apps.utility.utils import serialize_other_type_tree

from .models import (
    Bounty,
    Challenge,
    Initiative,
    Product,
    ProductArea,
    ProductContributorAgreementTemplate,
)


class ProductListView(ListView):
    model = Product
    template_name = "product_management/products.html"
    context_object_name = "products"
    queryset = Product.objects.filter(
        visibility=Product.Visibility.GLOBAL
    ).order_by("created_at")
    paginate_by = 8

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["challenge_status"] = Challenge.ChallengeStatus
        return context


class ProductRedirectView(utils.BaseProductDetailView, RedirectView):
    def get(self, request, *args, **kwargs):
        url = reverse("product_summary", kwargs=kwargs)
        return redirect(url)


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

        # Get the first ProductTree for the current product
        product_tree = product.product_trees.first()
        
        if product_tree:
            # Get all root ProductAreas associated with this ProductTree
            product_areas = ProductArea.get_root_nodes().filter(product_tree=product_tree)
            context["tree_data"] = [utils.serialize_tree(node) for node in product_areas]
        else:
            context["tree_data"] = []

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

        context["skills"] = [serialize_other_type_tree(skill) for skill in Skill.get_roots()]
        context["expertises"] = [serialize_other_type_tree(expertise) for expertise in expertises]
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
        product = context["product"]
        
        context["can_modify_product"] = utils.has_product_modify_permission(self.request.user, product)
        
        # Get the first ProductTree for the current product
        product_tree = product.product_trees.first()
        
        if product_tree:
            # Get all root ProductAreas associated with this ProductTree
            product_areas = ProductArea.get_root_nodes().filter(product_tree=product_tree)
            context["tree_data"] = [utils.serialize_tree(node) for node in product_areas]
        else:
            context["tree_data"] = []
        
        return context
    

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


class ChallengeDetailView(utils.BaseProductDetailView, common_mixins.AttachmentMixin, DetailView):
    model = Challenge
    context_object_name = "challenge"
    template_name = "product_management/challenge_detail.html"

    def get_object(self, queryset=None):
        try:
            return super().get_object(queryset)
        except Challenge.DoesNotExist:
            messages.error(self.request, "This challenge no longer exists.")
            raise Http404("Challenge does not exist")

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
        if len(form.cleaned_data.get("expertise_ids")) > 0:
            form.instance.expertise.add(
                *Expertise.objects.filter(id__in=form.cleaned_data.get("expertise_ids").split(","))
            )
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

    return redirect(reverse("portal-product-bounties", args=(instance.bounty.challenge.product.slug,)))


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
