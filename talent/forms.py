from django import forms
from django.contrib.auth.forms import UserCreationForm

from security.models import User


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


class SignUpForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)
        self.fields["password1"].widget = styled_input("password", "Password")
        self.fields["password2"].widget = styled_input("password", "Confirm Password")

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
        widgets = {
            "username": styled_input("text", "Username"),
            "email": styled_input("email", "Email"),
        }


class SignInForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=styled_input("text", "Username"),
    )
    password = forms.CharField(
        max_length=128,
        widget=styled_input("password", "Password"),
    )
