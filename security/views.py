from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.views.generic import TemplateView
from django.utils.translation import gettext_lazy as _
from formtools.wizard.views import SessionWizardView
from django.urls import reverse_lazy
from django.contrib.auth.views import (
    LogoutView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)

from .forms import ResetPasswordForm
from .models import User
from .forms import SignInForm, SignUpStepOneForm, SignUpStepTwoForm, SignUpStepThreeForm
from .services import SignUpRequestService, create_and_send_verification_code
from .constants import SIGN_UP_REQUEST_ID


class SignUpWizard(SessionWizardView):
    form_list = [SignUpStepOneForm, SignUpStepTwoForm, SignUpStepThreeForm]
    template_name = "security/sign_up.html"
    initial_dict = {"0": {}, "1": {}, "2": {}}

    def get_context_data(self, form, **kwargs):
        ctx = super().get_context_data(form=form, **kwargs)

        if self.steps.current == "1":
            cleaned_data = self.get_cleaned_data_for_step("0")
            email = cleaned_data.get("email")

            initial_form_data = self.initial_dict.get("1", None)

            req_id = None
            if initial_form_data:
                req_id = initial_form_data.get(SIGN_UP_REQUEST_ID)

            if not req_id:
                req_id = create_and_send_verification_code(email)

            self.initial_dict.get("1").update({SIGN_UP_REQUEST_ID: req_id})

        return ctx

    def done(self, form_list, **kwargs):
        sign_up_req_id = self.initial_dict.get("1").get(SIGN_UP_REQUEST_ID)
        SignUpRequestService.create_from_steps_form(form_list, sign_up_req_id)

        return redirect("challenges")


class SignInView(TemplateView):
    form_class = SignInForm
    initial = {}
    template_name = "security/sign_in.html"

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


class ResetPasswordView(PasswordResetView):
    form_class = ResetPasswordForm
    template_name = "security/reset_password.html"
    success_url = reverse_lazy("home")

    def get(self, request, *args, **kwargs):
        form = self.form_class(initial=self.initial)
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            email = form.cleaned_data["email"]
            if User.objects.filter(email=email).exists():
                return self.form_valid(form)
        else:
            form.add_error(None, _("TODO: add an error message"))

        return render(request, self.template_name, {"form": form})
