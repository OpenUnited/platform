from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from formtools.wizard.views import SessionWizardView

from .models import Person
from .forms import PersonDraftForm, EmailVerificationCodeForm, UsernameAndPasswordForm


def does_email_exist(wizard):
    cleaned_data = wizard.get_cleaned_data_for_step("0") or {}
    email = cleaned_data.get("email")

    return Person.objects.filter(email=email).exists()


class SignUpWizard(SessionWizardView):
    form_list = [PersonDraftForm, EmailVerificationCodeForm, UsernameAndPasswordForm]
    template_name = "talent/sign_up.html"

    def done(self, form_list, **kwargs):
        import ipdb

        ipdb.set_trace()
        print(form_list)
        return HttpResponse("test wizard success!")


def test(request):
    return HttpResponse("aaaaaa")


def sign_in(request):
    return HttpResponse("jlkşfslkdfsd")


def log_out(request):
    logout(request)
    return redirect("home")
