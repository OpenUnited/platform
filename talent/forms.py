from django import forms
from django.contrib.auth.forms import UserCreationForm

from talent.models import Talent


def styled_input(input_type, placeholder):
    """
    This function returns a TextInput or PasswordInput widget with predefined style.
    """
    attrs = {
        "class": "my-2 g-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500",
        "placeholder": placeholder,
    }

    if input_type == "password":
        return forms.PasswordInput(attrs=attrs)
    elif input_type == "email":
        return forms.EmailInput(attrs=attrs)
    else:
        return forms.TextInput(attrs=attrs)


def styled_input_new(input_type, placeholder):
    """
    This function returns a TextInput or PasswordInput widget with predefined style.
    """
    attrs = {
        "class": "w-full px-3 py-2 placeholder-gray-300 border border-gray-300 rounded-md focus:outline-none focus:ring focus:ring-indigo-100 focus:border-indigo-300",
        "placeholder": placeholder,
    }

    if input_type == "password":
        return forms.PasswordInput(attrs=attrs)
    elif input_type == "email":
        return forms.EmailInput(attrs=attrs)
    else:
        return forms.TextInput(attrs=attrs)


class SignUpForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)
        self.fields["password1"].widget = styled_input_new("password", "Password")
        self.fields["password2"].widget = styled_input_new(
            "password", "Confirm Password"
        )

    class Meta:
        model = Talent
        fields = (
            "first_name",
            "last_name",
            "username",
            "email",
            "password1",
            "password2",
        )
        widgets = {
            "first_name": styled_input_new("first_name", "First Name"),
            "last_name": styled_input_new("last_name", "Last Name"),
            "username": styled_input_new("text", "Username"),
            "email": styled_input_new("email", "Email"),
        }


class SignInForm(forms.Form):
    username = forms.CharField(
        max_length=150, widget=styled_input_new("username", "Enter your username")
    )
    password = forms.CharField(
        max_length=128, widget=styled_input_new("password", "Enter your password")
    )
