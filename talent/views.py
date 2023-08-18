import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic.edit import UpdateView

from .models import Person, Skill, Expertise
from .forms import PersonProfileForm
from .services import PersonService


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
        form = PersonProfileForm(
            request.POST, request.FILES, instance=request.user.person
        )
        if form.is_valid():
            form.save()

            # make sure there is at least one skill
            skill_ids = json.loads(request.POST.get("selected_skills"))
            print(skill_ids)

            # make sure there is at least one expertise
            expertise_ids = json.loads(request.POST.get("selected-expertise"))
            print(expertise_ids)
        return super().post(request, *args, **kwargs)


def get_skills(request):
    skill_queryset = Skill.objects.all().values()
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
