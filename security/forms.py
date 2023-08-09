from django import forms


class SignInForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "block w-full h-10 rounded-md border-0 py-1.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-1 focus:ring-inset focus:ring-gray-300 sm:text-sm sm:leading-6 focus-visible:outline-transparent",
                "placeholder": "Enter your username",
                "required": True,
                "autocapitalize": "none",
            }
        )
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
