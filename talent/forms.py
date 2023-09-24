from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Person, Feedback


def _get_text_input_class():
    return "pt-2 px-4 pb-3 w-full text-sm text-black border border-solid border-[#D9D9D9] focus:outline-none rounded-sm"


def _get_text_area_class():
    return "pt-2 px-4 pb-3 min-h-[104px] w-full text-sm text-black border border-solid border-[#D9D9D9] focus:outline-none rounded-sm"


def _get_text_input_class_for_link():
    return "block w-full h-full max-w-full rounded-r-sm shadow-none border border-solid border-[#D9D9D9] py-1.5 px-3 text-gray-900 text-sm ring-0 placeholder:text-gray-400 focus:ring-0 focus-visible:outline-none sm:text-sm sm:leading-6 h-9"


def _get_choice_box_class():
    return "w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"


class PersonProfileForm(forms.ModelForm):
    selected_skill_ids = forms.CharField(
        widget=forms.HiddenInput(
            attrs={"id": "selected-skills", "name": "selected-skills"}
        )
    )
    selected_expertise_ids = forms.CharField(
        widget=forms.HiddenInput(
            attrs={"id": "selected-expert", "name": "selected-expert"}
        )
    )

    class Meta:
        model = Person
        fields = [
            "full_name",
            "preferred_name",
            "photo",
            "headline",
            "overview",
            "current_position",
            "location",
            "github_link",
            "twitter_link",
            "linkedin_link",
            "website_link",
            "send_me_bounties",
        ]
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
            "photo": forms.FileInput(
                attrs={
                    "class": "hidden",
                    "type": "file",
                }
            ),
            "current_position": forms.TextInput(
                attrs={
                    "class": _get_text_input_class(),
                    "placeholder": "Where are you currently working at",
                }
            ),
            "headline": forms.TextInput(
                attrs={
                    "class": _get_text_input_class(),
                    "placeholder": "Briefly describe yourself",
                }
            ),
            "overview": forms.Textarea(
                attrs={
                    "class": _get_text_area_class(),
                    "placeholder": "Introduce your background",
                }
            ),
            "location": forms.TextInput(
                attrs={
                    "class": _get_text_input_class(),
                    "placeholder": "Tokyo, Japan",
                }
            ),
            "github_link": forms.TextInput(
                attrs={
                    "class": _get_text_input_class_for_link(),
                    "placeholder": "https://github.com/",
                }
            ),
            "twitter_link": forms.TextInput(
                attrs={
                    "class": _get_text_input_class_for_link(),
                    "placeholder": "https://twitter.com/",
                }
            ),
            "linkedin_link": forms.TextInput(
                attrs={
                    "class": _get_text_input_class_for_link(),
                    "placeholder": "https://linkedin.com/in/",
                }
            ),
            "website_link": forms.TextInput(
                attrs={
                    "class": _get_text_input_class_for_link(),
                    "placeholder": "https://",
                }
            ),
            "send_me_bounties": forms.CheckboxInput(
                attrs={
                    "class": _get_choice_box_class(),
                }
            ),
        }

        help_texts = {"send_me_bounties": "Get notified when a new bounty is added."}


class FeedbackForm(forms.ModelForm):
    stars = forms.CharField(
        widget=forms.HiddenInput(
            attrs={
                "id": "star-rating",
                "name": "star-rating",
                "display": "none",
            }
        )
    )

    class Meta:
        model = Feedback
        fields = ["message", "stars"]

        widgets = {
            "message": forms.Textarea(
                attrs={
                    "class": _get_text_area_class(),
                    "placeholder": "Write your feedback here",
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        stars = self.data.get("stars", None)
        try:
            star_rating = int(stars.split("-")[-1])
            cleaned_data["stars"] = star_rating
        except (AttributeError, ValueError):
            raise ValidationError(
                _(
                    "Something went wrong. The given star value should be in 'star-x' format where x is an integer."
                )
            )
        return cleaned_data
