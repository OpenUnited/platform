from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import HttpResponse, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.core.exceptions import ValidationError

from apps.common import mixins
from .forms import (
    BountyDeliveryAttemptForm, FeedbackForm, 
    PersonProfileForm, PersonSkillFormSet
)
from .services import (
    ProfileService, ShowcaseService, 
    FeedbackService, BountyDeliveryService,
    SkillService
)

# Profile Management Views
class UpdateProfileView(LoginRequiredMixin, UpdateView):
    form_class = PersonProfileForm
    context_object_name = "person"
    slug_field = "username"
    slug_url_kwarg = "username"
    template_name = "talent/profile.html"
    login_url = "sign_in"

    def get_template_names(self):
        htmx = self.request.htmx
        if htmx and self.request.GET.get("empty_form"):
            return ["talent/helper/empty_form.html"]
        if htmx:
            return ["talent/partials/partial_expertises.html"]
        return ["talent/profile.html"]

    def get_object(self):
        return ProfileService.get_user_profile(self.request.user.username)

    def get_context_data(self, **kwargs):
        context = {}
        person = self.get_object()
        
        if self.request.htmx:
            context = self._get_htmx_context(person)
        else:
            context = self._get_standard_context(person)

        return context

    def _get_htmx_context(self, person):
        context = {"pk": person.pk}
        index = self.request.GET.get("index")
        
        if skill_id := self.request.GET.get(f"skills-{index}-skill"):
            expertises = ProfileService.get_expertises_for_skill(skill_id)
            context["expertises"] = expertises
        else:
            context["empty_form"] = PersonSkillFormSet().empty_form
            context["skills"] = ProfileService.get_active_skills()

        context["index"] = index
        return context

    def _get_standard_context(self, person):
        skills = ProfileService.get_active_skills()
        return {
            "form": self.form_class(instance=person),
            "pk": person.pk,
            "photo_url": person.get_photo_url(),
            "skills": skills,
            "selected_skills": skills,
            "expertises": ProfileService.get_expertises_for_skill(None)
        }

    def form_valid(self, form):
        try:
            context = self.get_context_data()
            person_skill_formset = context["person_skill_formset"]
            
            if form.is_valid() and person_skill_formset.is_valid():
                ProfileService.update_profile(
                    person=self.request.user.person,
                    profile_data=form.cleaned_data,
                    skills_data=person_skill_formset.cleaned_data
                )
                messages.success(self.request, _("Profile updated successfully"))
                return HttpResponseRedirect(self.get_success_url())
        except ValidationError as e:
            messages.error(self.request, str(e))
        return self.form_invalid(form)

# Showcase Views
class TalentShowcase(TemplateView):
    template_name = "talent/showcase.html"

    def get(self, request, username, *args, **kwargs):
        user = get_object_or_404(self.User, username=username)
        person = user.person

        # todo: check the statuses
        bounty_claims_completed = BountyClaim.objects.filter(
            status=BountyClaim.Status.COMPLETED,
            person=person,
        ).select_related("bounty__challenge", "bounty__challenge__product")

        bounty_claims_claimed = BountyClaim.objects.filter(
            bounty__status=Bounty.BountyStatus.CLAIMED,
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
            "person_linkedin_link": global_utils.get_path_from_url(person.linkedin_link, True),
            "person_twitter_link": global_utils.get_path_from_url(person.twitter_link, True),
            "person_skills": person.skills.all().select_related("skill"),
            "bounty_claims_claimed": bounty_claims_claimed,
            "bounty_claims_completed": bounty_claims_completed,
            "FeedbackService": FeedbackService,
            "received_feedbacks": received_feedbacks,
            "form": FeedbackForm(),
            "can_leave_feedback": can_leave_feedback,
        }
        return self.render_to_response(context)

    def get_success_url(self):
        return reverse("showcase", args=(self.object.recipient.get_username(),))


@login_required(login_url="sign_in")
def get_current_skills(request):
    skill_ids = SkillService.get_current_skills(request.user.person)
    return JsonResponse(skill_ids, safe=False)


@login_required(login_url="sign_in")
def get_skills(request):
    skills = SkillService.get_all_active_skills()
    return JsonResponse(skills, safe=False)


class GetExpertiseView(LoginRequiredMixin, TemplateView):
    template_name = "talent/helper/expertises.html"
    login_url = "sign_in"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        skill_id = self.request.GET.get("skill")
        
        context.update(ProfileService.get_expertise_context(
            skill_id=skill_id,
            index=self.request.GET.get('index', 0)
        ))
        
        return context


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


def status_and_points(request):
    return HttpResponse("TODO")


class CreateFeedbackView(LoginRequiredMixin, CreateView):
    form_class = FeedbackForm
    template_name = "talent/partials/feedback_form.html"
    login_url = "sign_in"

    def get_success_url(self):
        return reverse("showcase", args=(self.object.recipient.get_username(),))

    def _get_recipient_from_url(self):
        recipient_username = self.request.headers.get("Referer").split("/")[-1]
        return ProfileService.get_user_profile(recipient_username)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "post_url": reverse("create-feedback"),
            "person": self._get_recipient_from_url(),
            "current_rating": 0,
        })
        return context

    def form_valid(self, form):
        try:
            self.object = FeedbackService.create(
                provider=self.request.user.person,
                recipient=self._get_recipient_from_url(),
                **form.cleaned_data
            )
            messages.success(self.request, _("Feedback created successfully"))
            return HttpResponseRedirect(self.get_success_url())
        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)


class UpdateFeedbackView(LoginRequiredMixin, UpdateView):
    form_class = FeedbackForm
    context_object_name = "feedback"
    template_name = "talent/partials/feedback_form.html"
    login_url = "sign_in"

    def get_success_url(self):
        return reverse("showcase", args=(self.object.recipient.get_username(),))

    def get_object(self):
        return FeedbackService.get_feedback(self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "post_url": reverse("update-feedback", args=(self.object.pk,)),
            "person": self.object.recipient,
            "current_rating": self.object.stars,
        })
        return context

    def form_valid(self, form):
        try:
            self.object = FeedbackService.update(
                feedback_id=self.object.pk,
                **form.cleaned_data
            )
            messages.success(self.request, _("Feedback updated successfully"))
            return HttpResponseRedirect(self.get_success_url())
        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)


class DeleteFeedbackView(LoginRequiredMixin, DeleteView):
    context_object_name = "feedback"
    template_name = "talent/partials/delete_feedback_form.html"
    login_url = "sign_in"

    def get_success_url(self):
        return reverse("showcase", args=(self.object.recipient.get_username(),))

    def get_object(self):
        return FeedbackService.get_feedback(self.kwargs['pk'])

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            FeedbackService.delete(
                feedback_id=self.object.pk,
                deleting_user=request.user.person
            )
            messages.success(self.request, _("Feedback is successfully deleted!"))
            return HttpResponseRedirect(self.get_success_url())
        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.get(request, *args, **kwargs)


class CreateBountyDeliveryAttemptView(LoginRequiredMixin, mixins.AttachmentMixin, CreateView):
    form_class = BountyDeliveryAttemptForm
    success_url = reverse_lazy("dashboard")
    template_name = "talent/bounty_claim_attempt.html"
    login_url = "sign_in"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def form_valid(self, form):
        try:
            self.object = BountyDeliveryService.create_delivery_attempt(
                person=self.request.user.person,
                bounty_claim=form.cleaned_data['bounty_claim'],
                attempt_data=form.cleaned_data
            )
            messages.success(self.request, _("Delivery attempt created successfully"))
            return HttpResponseRedirect(self.get_success_url())
        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)


class BountyDeliveryAttemptDetail(LoginRequiredMixin, mixins.AttachmentMixin, DetailView):
    template_name = "talent/bounty_delivery_attempt_detail.html"
    context_object_name = "object"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        attempt, is_admin = BountyDeliveryService.get_attempt_details(
            attempt_id=self.object.id,
            requesting_person=self.request.user.person
        )
        data["is_product_admin"] = is_admin
        return data

    def post(self, request, *args, **kwargs):
        try:
            action_value = request.POST.get("bounty-delivery-action")
            BountyDeliveryService.handle_delivery_action(
                attempt_id=self.get_object().id,
                action_value=action_value,
                admin_person=request.user.person
            )
            messages.success(request, _("Delivery attempt processed successfully"))
            return HttpResponseRedirect(reverse("dashboard"))
        except ValidationError as e:
            messages.error(request, str(e))
            return self.get(request, *args, **kwargs)
