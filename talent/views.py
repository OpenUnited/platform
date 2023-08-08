from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth import logout
from django.views.generic import TemplateView
from formtools.wizard.views import SessionWizardView

from .forms import SignUpStepOneForm, SignUpStepTwoForm, SignUpStepThreeForm, SignInForm
from security.services import SignUpRequestService
from .services import create_and_send_verification_code
from .constants import SIGN_UP_REQUEST_ID


class SignUpWizard(SessionWizardView):
    form_list = [SignUpStepOneForm, SignUpStepTwoForm, SignUpStepThreeForm]
    template_name = "talent/sign_up.html"
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

        return render(self.request, "product_management/challenges.html")


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
            return HttpResponse("home")

        return render(request, self.template_name, {"form": form})


def reset_password(request):
    return HttpResponse("reset password")


def log_out(request):
    logout(request)
    return redirect("home")
