import os
from django.shortcuts import HttpResponse, render
from django.views.generic.edit import UpdateView

from openunited import settings
from .models import Person
from .forms import PersonProfileForm

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
        person = self.get_queryset().first()
        initial = {
            "full_name": person.full_name,
            "preferred_name": person.preferred_name,
            "headline": person.headline,
            "overview": person.overview,
            "github_link": person.github_link,
            "twitter_link": person.twitter_link,
            "linkedin_link": person.linkedin_link,
            "website_link": person.website_link,
            "send_me_bounties": person.send_me_bounties,
            "current_position": person.current_position,
        }
        context["form"] = PersonProfileForm(initial=initial)
        image_url = (
            settings.MEDIA_URL + settings.PERSON_PHOTO_UPLOAD_TO + "profile-empty.png"
        )
        requires_upload = True

        if person.photo:
            image_url = person.photo.url
            requires_upload = False

        context["image"] = image_url
        context["requires_upload"] = requires_upload
        context["pk"] = person.pk
        return context

    def post(self, request, *args, **kwargs):
        form = PersonProfileForm(
            request.POST, request.FILES, instance=request.user.person
        )
        if form.is_valid():
            form.save()
        return super().post(request, *args, **kwargs)


def remove_picture(request, pk):
    person = request.user.person
    path = person.photo.path
    if os.path.exists(path):
        os.remove(path)

    person.photo.delete(save=True)

    initial = {
        "full_name": person.full_name,
        "preferred_name": person.preferred_name,
        "headline": person.headline,
        "overview": person.overview,
        "github_link": person.github_link,
        "twitter_link": person.twitter_link,
        "linkedin_link": person.linkedin_link,
        "website_link": person.website_link,
        "send_me_bounties": person.send_me_bounties,
        "current_position": person.current_position,
    }
    context = {
        "requires_upload": True,
        "image": settings.MEDIA_URL
        + settings.PERSON_PHOTO_UPLOAD_TO
        + "profile-empty.png",
        "pk": person.pk,
    }

    context["form"] = PersonProfileForm(initial=initial)

    return render(request, "talent/profile_picture.html", context)
