from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth import logout
from django.core.mail import send_mail
from random import randrange
from formtools.wizard.views import SessionWizardView

from security.models import VerificationCode
from .forms import SignUpStepOneForm, SignUpStepTwoForm, SignUpStepThreeForm
from security.services import SignUpRequestService

import ipdb


class SignUpWizard(SessionWizardView):
    form_list = [SignUpStepOneForm, SignUpStepTwoForm, SignUpStepThreeForm]
    template_name = "talent/sign_up.html"
    initial_dict = {
        "0": {},
        "1": {},
    }

    def get_context_data(self, form, **kwargs):
        ctx = super().get_context_data(form=form, **kwargs)

        if self.steps.current == "1":
            ipdb.set_trace()
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
                six_digit_number = randrange(100_000, 1_000_000)
                code = VerificationCode.objects.create(
                    verification_code=six_digit_number
                )
                self.initial_dict.get("1").update({"verification_code_id": code.id})
                print(code.id, six_digit_number)

            # send_mail(
            #     "Verification Code",
            #     f"Code: {verification_code}",
            #     None,
            #     ["dogukanteber1@hotmail.com"],
            # )

        return ctx

    def done(self, form_list, **kwargs):
        SignUpRequestService.create_from_steps_form(form_list)

        code_id = self.storage.extra_data.get("verification_code_id")
        VerificationCode.objects.filter(id=code_id).delete()

        return render(self.request, "product_management/challenges.html")


def sign_in(request):
    return HttpResponse("jlkşfslkdfsd")


def log_out(request):
    logout(request)
    return redirect("home")
