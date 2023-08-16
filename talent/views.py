from django.shortcuts import render
from django.views.generic.edit import UpdateView

from .models import Person
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
        return super().post(request, *args, **kwargs)
