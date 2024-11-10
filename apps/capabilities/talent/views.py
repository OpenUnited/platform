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
from django.conf import settings
from urllib.parse import urlparse

from apps.common import mixins
from .forms import (
    BountyDeliveryAttemptForm, FeedbackForm, 
    PersonProfileForm, PersonSkillFormSet
)
from .services import (
    ProfileService, ShowcaseService, 
    FeedbackService, BountyDeliveryService,
    SkillService, PersonStatusService
)
from .models import Person

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
class TalentShowcase(DetailView):
    template_name = "talent/showcase.html"
    model = Person
    context_object_name = 'person'
    
    def get_object(self):
        username = self.kwargs.get('username')
        User = get_user_model()
        user = get_object_or_404(User, username=username)
        return get_object_or_404(Person, user=user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        showcase_data = ShowcaseService.get_showcase_data(
            username=self.kwargs.get('username'),
            viewing_user=self.request.user
        )
        
        context.update(showcase_data)
        context['form'] = FeedbackForm()
        
        return context

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
    expertise_data = SkillService.get_person_expertise(request.user.person)
    return JsonResponse(expertise_data, safe=False)


@login_required(login_url="sign_in")
def list_skill_and_expertise(request):
    """Return skill and expertise pairs for given expertise IDs if request comes from allowed paths"""
    # Check if request comes from allowed paths
    referer = request.headers.get("Referer", "")
    if not referer:
        return JsonResponse([], safe=False)
        
    parsed_url = urlparse(referer)
    allowed_paths = ["/profile/"]
    if not any(path in parsed_url.path for path in allowed_paths):
        return JsonResponse([], safe=False)

    try:
        expertise_data = SkillService.get_skill_expertise_pairs(
            expertise_ids=request.GET.get("expertise"),
            skills=request.GET.get("skills")
        )
        return JsonResponse(expertise_data, safe=False)
    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required(login_url="sign_in")
def status_and_points(request):
    data = PersonStatusService.get_status_and_points(request.user.person)
    return JsonResponse(data)


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
