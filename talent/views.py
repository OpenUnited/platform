from django.shortcuts import HttpResponse, render
from django.views.generic.detail import DetailView
from django.contrib.staticfiles.storage import staticfiles_storage

from .models import Person
from .forms import PersonProfileForm


class ProfileView(DetailView):
    model = Person
    template_name = "talent/profile.html"
    context_object_name = "person"
    slug_field = "username"  # Use the 'username' field to look up the user
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
        image_url = staticfiles_storage.url("images/profile-empty.png")
        requires_upload = True

        if person.photo:
            image_url = person.photo.url
            requires_upload = False

        context["image"] = image_url
        context["requires_upload"] = requires_upload
        return context
