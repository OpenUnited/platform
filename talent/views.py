from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth import logout
from formtools.wizard.views import SessionWizardView

from .forms import SignUpStepOneForm, SignUpStepTwoForm, SignUpStepThreeForm
from security.services import SignUpRequestService


class SignUpWizard(SessionWizardView):
    form_list = [SignUpStepOneForm, SignUpStepTwoForm, SignUpStepThreeForm]
    template_name = "talent/sign_up.html"

    def done(self, form_list, **kwargs):
        SignUpRequestService.create_from_steps_form(form_list)

        return render(self.request, "product_management/challenges.html")


def sign_in(request):
    return HttpResponse("jlkşfslkdfsd")


def log_out(request):
    logout(request)
    return redirect("home")
