import json
from django.shortcuts import render, HttpResponse
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.generic.edit import UpdateView
from django.views.generic.base import TemplateView

from .models import Person, Skill, Expertise, PersonSkill, BountyClaim
from product_management.models import Challenge
from .forms import PersonProfileForm
from .services import PersonService, StatusService


import ipdb


class ProfileView(UpdateView):
    model = Person
    template_name = "talent/profile.html"
    fields = "__all__"
    context_object_name = "person"
    slug_field = "username"
    slug_url_kwarg = "username"

    def get_queryset(self):
        # Restrict the queryset to the currently authenticated user
        queryset = super().get_queryset()
        return queryset.filter(user__pk=self.request.user.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        person = self.get_object()
        context["form"] = PersonProfileForm(
            initial=PersonService.get_initial_data(person)
        )
        context["pk"] = person.pk

        image_url, requires_upload = PersonService.does_require_upload(person)
        context["image"] = image_url
        context["requires_upload"] = requires_upload

        return context

    def _remove_picture(self, request):
        person = self.get_object()
        PersonService.delete_photo(person)
        context = self.get_context_data()

        return render(request, "talent/profile_picture.html", context)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        trigger = request.headers.get("Hx-Trigger")
        if trigger == "remove_picture_button":
            return self._remove_picture(request)

        return super().get(request, *args, **kwargs)

    # TODO: Add a success message under the photo upload field
    def post(self, request, *args, **kwargs):
        person = request.user.person
        form = PersonProfileForm(request.POST, request.FILES, instance=person)
        if form.is_valid():
            form.save()

            person_skill = PersonSkill(person=person)
            skills_queryset = []
            selected_skills = request.POST.get("selected_skill_ids")
            if selected_skills:
                skill_ids = json.loads(selected_skills)
                skills_queryset = Skill.objects.filter(id__in=skill_ids).values_list(
                    "name", flat=True
                )
                person_skill.skill = list(skills_queryset)

            expertise_queryset = []
            selected_expertise = request.POST.get("selected_expertise_ids")
            if selected_expertise:
                expertise_ids = json.loads(selected_expertise)
                expertise_queryset = Expertise.objects.filter(
                    id__in=expertise_ids
                ).values_list("name", flat=True)
                person_skill.expertise = list(expertise_queryset)
                person_skill.save()

        return super().post(request, *args, **kwargs)


def get_skills(request):
    skill_queryset = (
        Skill.objects.filter(active=True).order_by("-display_boost_factor").values()
    )
    skills = list(skill_queryset)
    return JsonResponse(skills, safe=False)


def get_expertise(request):
    selected_skills = request.GET.get("selected_skills")
    if selected_skills:
        selected_skill_ids = json.loads(selected_skills)
        expertise_queryset = Expertise.objects.filter(
            skill_id__in=selected_skill_ids
        ).values()
        expertise = list(expertise_queryset)

        return JsonResponse(expertise, safe=False)

    return JsonResponse([], safe=False)


def list_skill_and_expertise(request):
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


# NOTE: The links in this view are not completed
class TalentPortfolio(TemplateView):
    User = get_user_model()
    template_name = "talent/portfolio.html"

    def get(self, request, username, *args, **kwargs):
        user = get_object_or_404(self.User, username=username)
        photo_url = "/media/avatars/profile-empty.png"
        person = user.person
        if person.photo:
            photo_url = person.photo.url

        status = person.status
        person_skill = PersonSkill.objects.get(person=person)
        bounty_claims = BountyClaim.objects.filter(
            person=person, bounty__challenge__status=Challenge.CHALLENGE_STATUS_DONE
        )

        context = {
            "user": user,
            "photo_url": photo_url,
            "person": person,
            "status": status,
            "PersonService": PersonService,
            "StatusService": StatusService,
            "skills": person_skill.skill,
            "expertise": person_skill.expertise,
            "bounty_claims": bounty_claims,
        }
        return self.render_to_response(context)


def status_and_points(request):
    return HttpResponse("TODO")
