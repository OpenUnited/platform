import json
from typing import Any
from django.shortcuts import render, HttpResponse
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.http import (
    Http404,
    HttpResponse,
    JsonResponse,
    HttpResponseRedirect,
)
from django.contrib import messages
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from utility import utils as global_utils
from talent import utils
from .models import (
    Person,
    Skill,
    Expertise,
    PersonSkill,
    BountyClaim,
    Feedback,
    BountyDeliveryAttempt,
)
from product_management.models import Product, Challenge, Bounty
from .forms import (
    PersonProfileForm,
    FeedbackForm,
    BountyDeliveryAttemptForm,
    PersonSkillFormSet,
)
from .services import FeedbackService


class UpdateProfileView(LoginRequiredMixin, UpdateView):
    model = Person
    form_class = PersonProfileForm
    context_object_name = "person"
    slug_field = "username"
    slug_url_kwarg = "username"
    login_url = "sign_in"

    def get_template_names(self):
        htmx = self.request.htmx
        if htmx and self.request.GET.get("empty_form"):
            return ["talent/helper/empty_form.html"]
        if htmx:
            return ["talent/partials/partial_expertises.html"]
        return ["talent/profile.html"]

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(user__pk=self.request.user.pk)

    def get_context_data(self, **kwargs):
        context = {}
        person = self.get_object()

        expertises = []
        context = {
            "pk": person.pk,
        }
        skills = [utils.serialize_skills(skill) for skill in Skill.get_roots()]

        if self.request.htmx:
            index = self.request.GET.get("index")
            if skill := self.request.GET.get(f"skills-{index}-skill"):
                expertises = [
                    utils.serialize_expertise(expertise)
                    for expertise in Expertise.get_roots().filter(skill=skill)
                ]
            else:
                context["empty_form"] = PersonSkillFormSet().empty_form
                context["skills"] = skills

            context["index"] = index
            context["expertises"] = expertises
        else:
            self.extract_context_data(person, context, skills)

        context["person_skill_formset"] = PersonSkillFormSet(
            self.request.POST or None,
            self.request.FILES or None,
            instance=person,
        )
        return context

    def extract_context_data(self, person, context, skills):
        context["form"] = self.form_class(instance=person)
        context["pk"] = person.pk
        context["photo_url"] = person.get_photo_url()
        context["skills"] = skills
        context["selected_skills"] = skills
        context["expertises"] = [
            utils.serialize_expertise(expertise)
            for expertise in Expertise.get_roots()
        ]

    def form_valid(self, form):
        person = self.request.user.person

        form = PersonProfileForm(
            self.request.POST, self.request.FILES, instance=person
        )
        context = self.get_context_data(**self.kwargs)
        person_skill_formset = context["person_skill_formset"]

        if form.is_valid() and person_skill_formset.is_valid():
            obj = form.save()
            person_skill_formset.instance = obj
            person_skill_formset.save()
        return super().form_valid(form)


@login_required(login_url="sign_in")
def get_skills(request):
    # TODO I don't think we need this
    skill_queryset = (
        Skill.objects.filter(active=True)
        .order_by("-display_boost_factor")
        .values()
    )
    skills = list(skill_queryset)
    return JsonResponse(skills, safe=False)


@login_required(login_url="sign_in")
def get_current_skills(request):
    # TODO I don't think we need this
    person = request.user.person
    try:
        person_skills = PersonSkill.objects.filter(person=person)
        skill_ids = []
        for person_skill in person_skills:
            skill_ids.append(person_skill.skill.id)
    except (ObjectDoesNotExist, AttributeError):
        skill_ids = []

    return JsonResponse(skill_ids, safe=False)


@login_required(login_url="sign_in")
def get_expertise(request):
    # TODO I don't think we need this

    selected_skills = request.GET.get("selected_skills")
    if selected_skills:
        selected_skill_ids = json.loads(selected_skills)
        expertise_queryset = Expertise.objects.filter(
            skill_id__in=selected_skill_ids
        ).values()

        person = request.user.person
        try:
            person_skills = PersonSkill.objects.filter(person=person)
            expertise_ids = []
            for person_skill in person_skills:
                for expertise in person_skill.expertise.all():
                    expertise_ids.append(expertise.id)
        except (ObjectDoesNotExist, AttributeError):
            expertise_ids = []

        return JsonResponse(
            {
                "expertiseList": list(expertise_queryset),
                "expertiseIDList": expertise_ids,
            },
            safe=False,
        )

    return JsonResponse(
        {
            "expertiseList": [],
            "expertiseIDList": [],
        },
        safe=False,
    )


@login_required(login_url="sign_in")
def get_current_expertise(request):
    # TODO I don't think we need this
    person = request.user.person
    try:
        person_skills = PersonSkill.objects.filter(person=person)
        expertise_ids = []
        for person_skill in person_skills:
            for expertise in person_skill.expertise.all():
                expertise_ids.append(expertise.id)

        print(expertise_ids)
        expertise = Expertise.objects.filter(id__in=expertise_ids).values()

    except (ObjectDoesNotExist, AttributeError):
        expertise_ids = []
        expertise = []

    return JsonResponse(
        {"expertiseList": list(expertise), "expertiseIDList": expertise_ids},
        safe=False,
    )


@login_required(login_url="sign_in")
def list_skill_and_expertise(request):
    # TODO I don't think we need this
    # Very basic pattern matching to enable this endpoint on
    # specific URLs.
    referer_url = request.headers.get("Referer")
    path = global_utils.get_path_from_url(referer_url)
    patterns = ["/profile/"]
    for pattern in patterns:
        if pattern not in path:
            return JsonResponse([], safe=False)

    skills = request.GET.get("skills")
    expertise = request.GET.get("expertise")

    if skills and expertise:
        expertise_ids = json.loads(expertise)
        expertise_queryset = Expertise.objects.filter(id__in=expertise_ids)

        skill_expertise_pairs = []
        for exp in expertise_queryset:
            pair = {
                "skill": exp.skill.name,
                "expertise": exp.name,
            }
            skill_expertise_pairs.append(pair)

        return JsonResponse(skill_expertise_pairs, safe=False)

    return JsonResponse([], safe=False)


class TalentPortfolio(TemplateView):
    User = get_user_model()
    template_name = "talent/portfolio.html"

    def get(self, request, username, *args, **kwargs):
        user = get_object_or_404(self.User, username=username)
        person = user.person

        person_skill = person.skills.all().first()
        # todo: check the statuses
        bounty_claims = BountyClaim.objects.filter(
            Q(status=BountyClaim.Status.COMPLETED)
            | Q(bounty__challenge__status=Challenge.CHALLENGE_STATUS_DONE)
            | Q(bounty__status=Bounty.BOUNTY_STATUS_CLAIMED),
            person=person,
        ).select_related("bounty__challenge", "bounty__challenge__product")

        received_feedbacks = Feedback.objects.filter(recipient=person)

        if (
            request.user.is_anonymous
            or request.user == user
            or received_feedbacks.filter(provider=request.user.person)
        ):
            can_leave_feedback = False
        else:
            can_leave_feedback = True

        context = {
            "user": user,
            "person": person,
            "person_linkedin_link": global_utils.get_path_from_url(
                person.linkedin_link, True
            ),
            "person_twitter_link": global_utils.get_path_from_url(
                person.twitter_link, True
            ),
            "status": person.status,
            "person_skills": PersonSkill.objects.all().select_related("skill"),
            "bounty_claims": bounty_claims,
            "FeedbackService": FeedbackService,
            "received_feedbacks": received_feedbacks,
            "form": FeedbackForm(),
            "can_leave_feedback": can_leave_feedback,
        }
        return self.render_to_response(context)


def status_and_points(request):
    return HttpResponse("TODO")


class CreateFeedbackView(LoginRequiredMixin, CreateView):
    model = Feedback
    form_class = FeedbackForm
    template_name = "talent/partials/feedback_form.html"
    login_url = "sign_in"

    def get_success_url(self):
        return reverse(
            "portfolio", args=(self.object.recipient.get_username(),)
        )

    def _get_recipient_from_url(self):
        recipient_username = self.request.headers.get("Referer").split("/")[-1]
        return Person.objects.get(user__username=recipient_username)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "post_url": reverse("create-feedback"),
                "person": self._get_recipient_from_url(),
                "current_rating": 0,
            }
        )

        return context

    def form_valid(self, form):
        form.instance.recipient = self._get_recipient_from_url()
        form.instance.provider = self.request.user.person
        self.object = form.save()

        messages.success(self.request, _("Feedback is successfully created!"))

        return super().form_valid(form)

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class UpdateFeedbackView(LoginRequiredMixin, UpdateView):
    model = Feedback
    form_class = FeedbackForm
    context_object_name = "feedback"
    template_name = "talent/partials/feedback_form.html"
    login_url = "sign_in"

    def get_success_url(self):
        return reverse(
            "portfolio", args=(self.object.recipient.get_username(),)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "post_url": reverse("update-feedback", args=(self.object.pk,)),
                "person": self.object.recipient,
                "current_rating": self.object.stars,
            }
        )

        return context

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.form_class(request.POST, instance=self.object)
        if form.is_valid():
            form.save()
            messages.success(
                self.request, _("Feedback is successfully updated!")
            )
            return HttpResponseRedirect(self.get_success_url())

        return super().post(request, *args, **kwargs)


class DeleteFeedbackView(LoginRequiredMixin, DeleteView):
    model = Feedback
    context_object_name = "feedback"
    template_name = "talent/partials/delete_feedback_form.html"
    login_url = "sign_in"

    def get_success_url(self):
        return reverse(
            "portfolio", args=(self.object.recipient.get_username(),)
        )

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        try:
            Feedback.objects.get(pk=self.object.pk).delete()
            messages.success(
                self.request, _("Feedback is successfully deleted!")
            )
            return HttpResponseRedirect(self.get_success_url())
        except ObjectDoesNotExist:
            return super().post(request, *args, **kwargs)


class CreateBountyDeliveryAttemptView(LoginRequiredMixin, CreateView):
    model = BountyDeliveryAttempt
    form_class = BountyDeliveryAttemptForm
    success_url = reverse_lazy("dashboard")
    template_name = "talent/bounty_claim_attempt.html"
    login_url = "sign_in"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request

        return kwargs

    # todo: find a better way to check if the page exists
    def get(self, request, *args, **kwargs):
        product_slug = kwargs.get("product_slug")
        challenge_id = kwargs.get("challenge_id")
        bounty_id = kwargs.get("bounty_id")

        product = get_object_or_404(
            Product,
            slug=product_slug,
        )

        challenge = get_object_or_404(
            Challenge,
            id=challenge_id,
        )

        bounty = get_object_or_404(
            Bounty,
            id=bounty_id,
        )

        if product != challenge.product or challenge != bounty.challenge:
            raise Http404("No matches the given query.")

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES, request=request)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.person = request.user.person
            instance.kind = BountyDeliveryAttempt.SUBMISSION_TYPE_NEW
            instance.save()

            bounty_claim = instance.bounty_claim
            bounty_claim.status = BountyClaim.Status.CONTRIBUTED
            bounty_claim.save()

            return HttpResponseRedirect(self.success_url)

        return super().post(request, *args, **kwargs)


class BountyDeliveryAttemptDetail(DetailView):
    model = BountyDeliveryAttempt
    context_object_name = "object"
    template_name = "talent/bounty_delivery_attempt_detail.html"

    TRIGGER_KEY = "bounty-delivery-action"
    APPROVE_TRIGGER_NAME = "approve-bounty-claim-delivery"
    REJECT_TRIGGER_NAME = "reject-bounty-claim-delivery"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        value = request.POST.get(self.TRIGGER_KEY)
        success = False
        if value == self.APPROVE_TRIGGER_NAME:
            self.object.kind = BountyDeliveryAttempt.SUBMISSION_TYPE_APPROVED
            success = True
        elif value == self.REJECT_TRIGGER_NAME:
            self.object.kind = BountyDeliveryAttempt.SUBMISSION_TYPE_REJECTED
            success = True

        if success:
            self.object.save()
            return HttpResponseRedirect(reverse("dashboard"))

        return super().post(request, *args, **kwargs)
