from django import forms

from .models import Person


class PersonProfileForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = (
            "full_name",
            "preferred_name",
            "photo",
            "headline",
            "overview",
            "github_link",
            "twitter_link",
            "linkedin_link",
            "website_link",
        )
        widgets = {
            "full_name": forms.TextInput(
                attrs={
                    "class": "py-1.5 px-3 text-sm text-black border border-solid border-[#D9D9D9] rounded-sm focus:outline-none",
                    "placeholder": "Your full name",
                    "autocapitalize": "none",
                }
            ),
            "preferred_name": forms.TextInput(
                attrs={
                    "class": "py-1.5 px-3 text-sm text-black border border-solid border-[#D9D9D9] rounded-sm focus:outline-none",
                    "placeholder": "Your preferred name",
                    "autocapitalize": "none",
                }
            ),
            "headline": forms.TextInput(
                attrs={
                    "class": "pt-2 px-4 pb-3 w-full text-sm text-black border border-solid border-[#D9D9D9] focus:outline-none rounded-sm",
                    "placeholder": "Briefly describe yourself",
                }
            ),
            "overview": forms.Textarea(
                attrs={
                    "class": "pt-2 px-4 pb-3 min-h-[104px] w-full text-sm text-black border border-solid border-[#D9D9D9] focus:outline-none rounded-sm",
                    "placeholder": "Introduce your background",
                }
            ),
            "github_link": forms.TextInput(
                attrs={
                    "class": "block w-full h-full max-w-full rounded-r-sm shadow-none border border-solid border-[#D9D9D9] py-1.5 px-3 text-gray-900 text-sm ring-0 placeholder:text-gray-400 focus:ring-0 focus-visible:outline-none sm:text-sm sm:leading-6 h-9",
                    "placeholder": "https://github.com/",
                }
            ),
            "twitter_link": forms.TextInput(
                attrs={
                    "class": "block w-full h-full max-w-full rounded-r-sm shadow-none border border-solid border-[#D9D9D9] py-1.5 px-3 text-gray-900 text-sm ring-0 placeholder:text-gray-400 focus:ring-0 focus-visible:outline-none sm:text-sm sm:leading-6 h-9",
                    "placeholder": "https://twitter.com/",
                }
            ),
            "linkedin_link": forms.TextInput(
                attrs={
                    "class": "block w-full h-full max-w-full rounded-r-sm shadow-none border border-solid border-[#D9D9D9] py-1.5 px-3 text-gray-900 text-sm ring-0 placeholder:text-gray-400 focus:ring-0 focus-visible:outline-none sm:text-sm sm:leading-6 h-9",
                    "placeholder": "https://linkedin.com/in/",
                }
            ),
            "website_link": forms.TextInput(
                attrs={
                    "class": "block w-full h-full max-w-full rounded-r-sm shadow-none border border-solid border-[#D9D9D9] py-1.5 px-3 text-gray-900 text-sm ring-0 placeholder:text-gray-400 focus:ring-0 focus-visible:outline-none sm:text-sm sm:leading-6 h-9",
                    "placeholder": "https://",
                }
            ),
        }
