from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth import logout
from formtools.wizard.views import SessionWizardView

from .forms import SignUpStepOneForm, SignUpStepTwoForm, SignUpStepThreeForm
from security.services import SignUpRequestService, VerificationCodeService
from .services import create_and_send_verification_code


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

            previous_code_id = None
            if initial_form_data:
                previous_code_id = initial_form_data.get("verification_code_id")

            if previous_code_id:
                self.initial_dict.get("1").update(
                    {"verification_code_id": previous_code_id}
                )
            else:
                code_id = create_and_send_verification_code(email)
                self.initial_dict.get("1").update({"verification_code_id": code_id})

        return ctx

    def done(self, form_list, **kwargs):
        SignUpRequestService.create_from_steps_form(form_list)

        # Deleting the temporarily created VerificationCode instance
        # since this object is only needed for sign up
        code_id = self.storage.extra_data.get("verification_code_id")
        VerificationCodeService.delete(code_id)

        return render(self.request, "product_management/challenges.html")


def sign_in(request):
    return HttpResponse("jlkşfslkdfsd")


def log_out(request):
    logout(request)
    return redirect("home")
