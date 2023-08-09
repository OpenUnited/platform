from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.views.generic import TemplateView
from django.utils.translation import gettext_lazy as _
from formtools.wizard.views import SessionWizardView

from .forms import SignInForm
from security.services import SignUpRequestService


class SignInView(TemplateView):
    form_class = SignInForm
    initial = {}
    template_name = "talent/sign_in.html"

    def get(self, request, *args, **kwargs):
        form = self.form_class(initial=self.initial)
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect("home")
            else:
                form.add_error(None, _("Username or password is not correct"))

        return render(request, self.template_name, {"form": form})
