from django import forms
from django.contrib.auth.forms import UserCreationForm

from talent.models import Profile


def styled_input(input_type, placeholder):
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
    elif input_type == "textarea":
        return forms.Textarea(attrs=attrs)
    elif input_type == "file":
        attrs[
            "class"
        ] = "relative m-0 block w-full min-w-0 flex-auto rounded border border-solid border-neutral-300 bg-clip-padding px-3 py-[0.32rem] text-base font-normal text-neutral-700 transition duration-300 ease-in-out file:-mx-3 file:-my-[0.32rem] file:overflow-hidden file:rounded-none file:border-0 file:border-solid file:border-inherit file:bg-neutral-100 file:px-3 file:py-[0.32rem] file:text-neutral-700 file:transition file:duration-150 file:ease-in-out file:[border-inline-end-width:1px] file:[margin-inline-end:0.75rem] hover:file:bg-neutral-200 focus:border-primary focus:text-neutral-700 focus:shadow-te-primary focus:outline-none dark:border-neutral-600 dark:text-neutral-200 dark:file:bg-neutral-700 dark:file:text-neutral-100 dark:focus:border-primary"
        return forms.FileInput(attrs=attrs)
    else:
        return forms.TextInput(attrs=attrs)


class SignUpForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
        self.fields["email"].required = True
        self.fields["password1"].widget = styled_input("password", "Password")
        self.fields["password2"].widget = styled_input("password", "Confirm Password")

    class Meta:
        model = Profile
        fields = (
            "first_name",
            "last_name",
            "username",
            "email",
            "password1",
            "password2",
        )
        widgets = {
            "first_name": styled_input("first_name", "First Name"),
            "last_name": styled_input("last_name", "Last Name"),
            "username": styled_input("text", "Username"),
            "email": styled_input("email", "Email"),
        }


class ProfileDetailsForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = (
            "headline",
            "overview",
            "photo",
        )

        widgets = {
            "headline": styled_input("headline", "Insert something"),
            "overview": styled_input("textarea", "Lorem ipsum sit amet"),
            "photo": styled_input("file", ""),
        }


class SignInForm(forms.Form):
    username = forms.CharField(
        max_length=150, widget=styled_input("username", "Enter your username")
    )
    password = forms.CharField(
        max_length=128, widget=styled_input("password", "Enter your password")
    )
