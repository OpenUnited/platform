from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm

from .models import User
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
    preferred_name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "block w-full h-10 rounded-md border-0 py-1.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-1 focus:ring-inset focus:ring-gray-300 sm:text-sm sm:leading-6 focus-visible:outline-transparent",
                "placeholder": "Your first name or what you like to be called",
                "autocomplete": "preferred-name",
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
            User.objects.filter(email=email).exists()
            or SignUpRequest.objects.filter(user__email=email).exists()
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

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(_("Username already exists"))

        return username

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


class SignInForm(forms.Form):
    username_or_email = forms.CharField(
        label="Username or E-mail",
        widget=forms.TextInput(
            attrs={
                "class": "block w-full h-10 rounded-md border-0 py-1.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-1 focus:ring-inset focus:ring-gray-300 sm:text-sm sm:leading-6 focus-visible:outline-transparent",
                "placeholder": "Enter your username or your e-mail",
                "required": True,
                "autocapitalize": "none",
            }
        ),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "block w-full h-10 rounded-md border-0 py-1.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-1 focus:ring-inset focus:ring-gray-300 sm:text-sm sm:leading-6 focus-visible:outline-transparent",
                "placeholder": "••••••",
                "required": True,
                "autocapitalize": "none",
            }
        )
    )
    remember_me = forms.BooleanField(required=False)


class PasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["email"].widget.attrs.update(
            {
                "class": "block w-full h-10 rounded-md border-0 py-1.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-1 focus:ring-inset focus:ring-gray-300 sm:text-sm sm:leading-6 focus-visible:outline-transparent",
                "placeholder": "Enter your email",
                "required": True,
            }
        )


class SetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["new_password1"].widget.attrs.update(
            {
                "class": "block w-full h-10 rounded-md border-0 py-1.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-1 focus:ring-inset focus:ring-gray-300 sm:text-sm sm:leading-6 focus-visible:outline-transparent",
                "required": True,
            }
        )
        self.fields["new_password2"].widget.attrs.update(
            {
                "class": "block w-full h-10 rounded-md border-0 py-1.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-1 focus:ring-inset focus:ring-gray-300 sm:text-sm sm:leading-6 focus-visible:outline-transparent",
                "required": True,
            }
        )
