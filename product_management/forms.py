from datetime import date
from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


from commerce.models import Organisation
from talent.models import BountyClaim
from .models import Idea, Product


class DateInput(forms.DateInput):
    input_type = "date"


class BountyClaimForm(forms.ModelForm):
    are_terms_accepted = forms.BooleanField(label=_("Do you accept the terms?"))

    class Meta:
        model = BountyClaim
        fields = ["expected_finish_date"]

        widgets = {
            "expected_finish_date": DateInput(),
        }

    def clean_expected_finish_date(self):
        finish_date = self.cleaned_data.get("expected_finish_date")

        if finish_date < date.today():
            raise ValidationError(
                _("Expected finish date cannot be earlier than today")
            )

        return finish_date


class IdeaForm(forms.ModelForm):
    class Meta:
        model = Idea
        fields = ["title", "description"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "pt-2 px-4 pb-3 w-full text-sm text-black border border-solid border-[#D9D9D9] focus:outline-none rounded-sm",
                    "placeholder": "Write the title of your idea",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "pt-2 px-4 pb-3 min-h-[104px] w-full text-sm text-black border border-solid border-[#D9D9D9] focus:outline-none rounded-sm",
                    "placeholder": "Describe your idea in detail",
                }
            ),
        }


class ProductForm(forms.ModelForm):
    # TODO: set up a hierarcy in organisation and query accordingly
    owner = forms.ModelChoiceField(
        empty_label="Select an organisation",
        queryset=Organisation.objects.all(),
        to_field_name="name",
        widget=forms.Select(
            attrs={
                "class": "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6",
            }
        ),
        help_text="Optional. If you do not provide an organisation, you will be the owner of the product",
    )

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        if request and request.user.is_authenticated:
            self.fields["owner"].queryset = Organisation.objects.filter(
                person=request.user.person
            )

    def clean_photo(self):
        photo = self.cleaned_data.get("photo")

        allowed_extensions = [".jpg", "jpeg", "png"]
        if photo:
            file_name = photo.name
            file_extension = file_name.split(".")[-1]
            if file_extension not in allowed_extensions:
                raise ValidationError(
                    _(
                        f"File extension must be one of the following: {' '.join(allowed_extensions)}"
                    )
                )

    class Meta:
        model = Product
        exclude = [
            "slug",
            "capability_start",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "block w-full pl-2 rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
                    "autocomplete": "none",
                }
            ),
            "short_description": forms.TextInput(
                attrs={
                    "class": "block w-full pl-2 rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
                }
            ),
            "full_description": forms.Textarea(
                attrs={
                    "class": "block w-full pl-2 rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
                }
            ),
            "website": forms.URLInput(
                attrs={
                    "class": "block flex-1 border-0 bg-transparent py-1.5 pl-1 text-gray-900 placeholder:text-gray-400 focus:ring-0 sm:text-sm sm:leading-6",
                }
            ),
            "detail_url": forms.URLInput(
                attrs={
                    "class": "block flex-1 border-0 bg-transparent py-1.5 pl-1 text-gray-900 placeholder:text-gray-400 focus:ring-0 sm:text-sm sm:leading-6",
                    "placeholder": "",
                }
            ),
            "video_url": forms.URLInput(
                attrs={
                    "class": "block flex-1 border-0 bg-transparent py-1.5 pl-1 text-gray-900 placeholder:text-gray-400 focus:ring-0 sm:text-sm sm:leading-6",
                    "placeholder": "",
                }
            ),
            "is_private": forms.CheckboxInput(
                attrs={
                    "class": "h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600",
                }
            ),
            "photo": forms.FileInput(
                attrs={
                    "class": "rounded-md bg-white px-2.5 py-1.5 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50",
                }
            ),
            "attachment": forms.FileInput(
                attrs={
                    "class": "",
                }
            ),
        }
        labels = {
            "detail_url": "Additional URL",
            "video_url": "Video URL",
            "is_private": "Private",
        }

        help_texts = {
            "short_description": "Explain the product in one or two sentences.",
            "full_description": "Give as much detail as you want about the product.",
            "website": "Link to the product's website, if any.",
            "video_url": "Link to a video such as Youtube.",
            "is_private": "Make the product private",
        }


class OrganisationForm(forms.ModelForm):
    class Meta:
        model = Organisation
        exclude = ["id"]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "block w-full pl-2 rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
                }
            ),
            "username": forms.TextInput(
                attrs={
                    "class": "block w-full pl-2 rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
                }
            ),
            "photo": forms.FileInput(
                attrs={
                    "class": "rounded-md bg-white px-2.5 py-1.5 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50",
                }
            ),
        }
