from django import forms

from .models import PersonDraft


class PersonDraftForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["full_name"].widget.attrs.update(
            {
                "class": "block w-full h-10 rounded-md border-0 py-1.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-1 focus:ring-inset focus:ring-gray-300 sm:text-sm sm:leading-6 focus-visible:outline-transparent",
                "placeholder": "Enter your full name",
                "autocomplete": "full-name",
                "required": True,
                "autocapitalize": "none",
            }
        )
        self.fields["email"].widget.attrs.update(
            {
                "class": "block w-full h-10 rounded-md border-0 py-1.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-1 focus:ring-inset focus:ring-gray-300 sm:text-sm sm:leading-6 focus-visible:outline-transparent",
                "placeholder": "Enter your email",
                "autocomplete": "email",
                "required": True,
            }
        )

    class Meta:
        model = PersonDraft
        fields = [
            "full_name",
            "email",
        ]


class EmailVerificationCodeForm(forms.Form):
    verification_code = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "autocomplete": "one-time-code",
                "inputmode": "numeric",
                "maxlength": "6",
                "pattern": "\d{6}",
            }
        )
    )


class UsernameAndPasswordForm(forms.Form):
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
    password1 = forms.CharField(
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
    password2 = forms.CharField(
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
