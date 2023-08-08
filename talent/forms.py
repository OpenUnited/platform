from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.password_validation import validate_password
from django.forms import ValidationError

from .models import Person
from .constants import SIGN_UP_REQUEST_ID
from security.models import SignUpRequest


class SignUpStepOneForm(forms.Form):
    full_name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "block w-full h-10 rounded-md border-0 py-1.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-1 focus:ring-inset focus:ring-gray-300 sm:text-sm sm:leading-6 focus-visible:outline-transparent",
                "placeholder": "Enter your full name",
                "autocomplete": "full-name",
                "required": True,
                "autocapitalize": "none",
            }
        )
    )
    email = forms.CharField(
        widget=forms.EmailInput(
            attrs={
                "class": "block w-full h-10 rounded-md border-0 py-1.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-1 focus:ring-inset focus:ring-gray-300 sm:text-sm sm:leading-6 focus-visible:outline-transparent",
                "placeholder": "Enter your email",
                "autocomplete": "email",
                "required": True,
            }
        )
    )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if (
            Person.objects.filter(email=email).exists()
            or SignUpRequest.objects.filter(email=email).exists()
        ):
            raise forms.ValidationError(
                _("That email isn't available, please try another")
            )

        return email


class SignUpStepTwoForm(forms.Form):
    verification_code = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "autofocus": True,
                "autocomplete": "one-time-code",
                "inputmode": "numeric",
                "maxlength": "6",
                "pattern": "\d{6}",
            }
        )
    )

    def clean(self):
        cleaned_data = super().clean()
        verification_code = cleaned_data.get("verification_code")

        req_id = self.initial.get(SIGN_UP_REQUEST_ID)

        actual_verification_code = SignUpRequest.objects.get(id=req_id)

        if verification_code != actual_verification_code.verification_code:
            print(verification_code, actual_verification_code.verification_code)
            raise ValidationError(_("Invalid verification code. Please try again."))

        return cleaned_data


class SignUpStepThreeForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "block w-full h-10 rounded-md border-0 py-1.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-1 focus:ring-inset focus:ring-gray-300 sm:text-sm sm:leading-6 focus-visible:outline-transparent",
                "name": "username",
                "required": True,
                "placeholder": "Enter your username",
                "autocapitalize": "none",
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "id": "password-checker-field",
                "class": "block w-full h-10 rounded-md border-0 py-1.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-1 focus:ring-inset focus:ring-gray-300 sm:text-sm sm:leading-6 focus-visible:outline-transparent",
                "placeholder": "••••••",
                "name": "password",
                "required": True,
                "autocapitalize": "none",
            }
        )
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "block w-full h-10 rounded-md border-0 py-1.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-1 focus:ring-inset focus:ring-gray-300 sm:text-sm sm:leading-6 focus-visible:outline-transparent",
                "placeholder": "••••••",
                "name": "password",
                "required": True,
                "autocapitalize": "none",
            }
        )
    )

    def clean_password(self):
        password = self.cleaned_data.get("password")

        validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password != password_confirm:
            raise forms.ValidationError(_("Passwords have to match"))
