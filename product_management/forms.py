import json
from datetime import date
from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.urls import reverse_lazy
from django.core.exceptions import ObjectDoesNotExist


from commerce.models import Organisation
from talent.models import BountyClaim, Person
from .models import Idea, Product, Challenge, Bounty
from security.models import ProductRoleAssignment


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
    organisation = forms.ModelChoiceField(
        empty_label="Select an organisation",
        required=False,
        queryset=Organisation.objects.none(),
        to_field_name="name",
        label="Organisations",
        widget=forms.Select(
            attrs={
                "class": "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6",
            }
        ),
    )
    make_me_owner = forms.BooleanField(
        label="Make me the owner",
        widget=forms.CheckboxInput(
            attrs={
                "class": "h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600",
            }
        ),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super(ProductForm, self).__init__(*args, **kwargs)
        self.fields["content_type"].required = False
        self.fields["object_id"].required = False

    def clean_name(self):
        name = self.cleaned_data.get("name")
        error = Product.check_slug_from_name(name)
        if error:
            raise ValidationError(error)

        return name

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
                    "hx-post": reverse_lazy("create-product"),
                    "hx-trigger": "input delay:100ms",
                    "hx-select": "#name-errors",
                    "hx-target": "#name-errors",
                    "hx-swap": "innerHTML",
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
            "content_object": "Owner",
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
                    "hx-post": reverse_lazy("create-organisation"),
                    "hx-trigger": "input",
                    "hx-target": "#organisation-name-errors",
                    "hx-select": "#organisation-name-errors",
                    "hx-indicator": "#ind-name",
                }
            ),
            "username": forms.TextInput(
                attrs={
                    "class": "block w-full pl-2 rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
                    "hx-post": reverse_lazy("create-organisation"),
                    "hx-trigger": "input",
                    "hx-target": "#organisation-username-errors",
                    "hx-select": "#organisation-username-errors",
                    "hx-indicator": "#ind-username",
                }
            ),
            "photo": forms.FileInput(
                attrs={
                    "class": "rounded-md bg-white px-2.5 py-1.5 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50",
                }
            ),
        }

    def clean_name(self):
        name = self.cleaned_data.get("name")

        try:
            Organisation.objects.get(name=name)
            raise ValidationError(_("This name already taken."))
        except ObjectDoesNotExist:
            return name

    def clean_username(self):
        username = self.cleaned_data.get("username")

        if Organisation.objects.filter(username=username) or Person.objects.filter(
            user__username=username
        ):
            raise ValidationError(_("This username is already taken."))

        return username


class ChallengeForm(forms.ModelForm):
    product = forms.ModelChoiceField(
        empty_label="Select a product",
        queryset=Product.objects.all(),
        widget=forms.Select(
            attrs={
                "class": "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6",
                # "hx-get": reverse_lazy("get-people-of-product"),
                # "hx-target": "#id_reviewer",
                # "hx-swap": "outerHTML",
            }
        ),
    )
    # TODO: limit this with ProductRoleAssignment
    # reviewer = forms.ModelChoiceField(
    #     empty_label="Select a reviewer",
    #     queryset=ProductRoleAssignment.objects.none(),
    #     widget=forms.Select(
    #         attrs={
    #             "class": "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6",
    #         }
    #     ),
    # )

    class Meta:
        model = Challenge
        fields = [
            "title",
            "description",
            "product",
            "reward_type",
            "priority",
            "status",
        ]

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "block w-full rounded-md border-0 p-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "block w-full rounded-md border-0 p-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
                }
            ),
            "reward_type": forms.RadioSelect(
                attrs={
                    "class": "h-4 w-4 border-gray-300 text-indigo-600 focus:ring-indigo-600",
                }
            ),
            "priority": forms.Select(
                attrs={
                    "class": "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6",
                },
                choices=Challenge.CHALLENGE_PRIORITY,
            ),
            "status": forms.Select(
                attrs={
                    "class": "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6",
                },
                choices=Challenge.CHALLENGE_STATUS,
            ),
        }

        help_texts = {
            "reward_type": "Liquid points can be redeemed for money, Non-Liquid points cannot.",
        }


class BountyForm(forms.ModelForm):
    challenge = forms.ModelChoiceField(
        empty_label="Select a challenge",
        queryset=Challenge.objects.filter(status=Challenge.CHALLENGE_STATUS_AVAILABLE),
        widget=forms.Select(
            attrs={
                "class": "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6",
            }
        ),
    )
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

    def clean_challenge(self):
        challenge = self.cleaned_data.get("challenge")

        if challenge.has_bounty():
            raise ValidationError(
                _(
                    "This challenge has already bounty on it. To create this bounty, either delete the current bounty or create another challenge."
                )
            )

        return challenge

    def clean_selected_skill_ids(self):
        skill_id = self.cleaned_data.get("selected_skill_ids")
        skill_id = json.loads(skill_id)

        if len(skill_id) != 1:
            raise ValidationError(_("You must select exactly one skill."))

        return skill_id

    def clean_selected_expertise_ids(self):
        expertise_ids = self.cleaned_data.get("selected_expertise_ids")

        return json.loads(expertise_ids)

    class Meta:
        model = Bounty
        fields = ["points", "status", "is_active"]

        widgets = {
            "points": forms.NumberInput(
                attrs={
                    "class": "block w-full rounded-md border-0 p-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6",
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600",
                }
            ),
        }

        help_texts = {
            "is_active": "Display this bounty under the challenge that is created for."
        }

        labels = {
            "is_active": "Is Active",
        }
