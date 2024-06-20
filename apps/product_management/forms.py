import json
from datetime import date

from django import forms
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.forms import modelformset_factory
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from tinymce.widgets import TinyMCE

from apps.commerce.models import Organisation
from apps.security.models import ProductRoleAssignment
from apps.talent.models import BountyClaim, Person
from apps.utility import utils as global_utils

from .models import Bounty, Bug, Challenge, Idea, Initiative, Product, ProductArea, ProductContributorAgreementTemplate


class DateInput(forms.DateInput):
    input_type = "date"


class BountyClaimForm(forms.ModelForm):
    is_agreement_accepted = forms.BooleanField(label=_("I have read and agree to the Contribution Agreement"))

    class Meta:
        model = BountyClaim
        fields = ["expected_finish_date"]
        labels = {
            "expected_finish_date": "Expected Submission Date",
        }

        widgets = {
            "expected_finish_date": DateInput(),
        }

    def clean_expected_finish_date(self):
        finish_date = self.cleaned_data.get("expected_finish_date")

        if finish_date < date.today():
            raise ValidationError(_("Expected finish date cannot be earlier than today"))

        return finish_date


class IdeaForm(forms.ModelForm):
    class Meta:
        model = Idea
        fields = ["title", "description"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": (
                        "pt-2 px-4 pb-3 w-full text-sm text-black border border-solid border-[#D9D9D9]"
                        " focus:outline-none rounded-sm"
                    ),
                    "placeholder": "Write the title of your idea",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": (
                        "pt-2 px-4 pb-3 min-h-[104px] w-full text-sm text-black border border-solid border-[#D9D9D9]"
                        " focus:outline-none rounded-sm"
                    ),
                    "placeholder": "Describe your idea in detail",
                }
            ),
        }


class BugForm(forms.ModelForm):
    class Meta:
        model = Bug
        fields = ["title", "description"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": (
                        "pt-2 px-4 pb-3 w-full text-sm text-black border border-solid border-[#D9D9D9]"
                        " focus:outline-none rounded-sm"
                    ),
                    "placeholder": "Write the title of the bug",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": (
                        "pt-2 px-4 pb-3 min-h-[104px] w-full text-sm text-black border border-solid border-[#D9D9D9]"
                        " focus:outline-none rounded-sm"
                    ),
                    "placeholder": "Describe the bug in detail",
                }
            ),
        }


class ProductForm(forms.ModelForm):
    organisation = forms.ModelChoiceField(
        empty_label="Select an organisation",
        required=False,
        # TODO: We should not get all the organizations here.
        # After the organization hierarchy is constructed, we need to filter based on the current user's organizations.
        queryset=Organisation.objects.all(),
        to_field_name="name",
        label="Organisations",
        widget=forms.Select(
            attrs={
                "class": (
                    "block w-full rounded-md border-0 p-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300"
                    " focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
                ),
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
        # skip slug validation if name is not changed in update view
        if self.instance and self.instance.name == name:
            return name

        if error := Product.check_slug_from_name(name):
            raise ValidationError(error)

        return name

    def clean(self):
        cleaned_data = super().clean()
        make_me_owner = cleaned_data.get("make_me_owner")
        organisation = cleaned_data.get("organisation")

        if make_me_owner and organisation:
            self.add_error(
                "organisation",
                "A product cannot be owned by a person and an organisation",
            )
            return cleaned_data

        if not make_me_owner and not organisation:
            self.add_error(
                "organisation",
                "You have to select an owner",
            )
            return cleaned_data

        if make_me_owner:
            cleaned_data["content_type"] = ContentType.objects.get_for_model(self.request.user.person)
            cleaned_data["object_id"] = self.request.user.id
        else:
            cleaned_data["content_type"] = ContentType.objects.get_for_model(organisation)
            cleaned_data["object_id"] = organisation.id

        return cleaned_data

    class Meta:
        model = Product
        exclude = [
            "slug",
            "capability_start",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": global_utils.text_field_class_names,
                    "autocomplete": "none",
                    "hx-post": reverse_lazy("create-product"),
                    "hx-trigger": "input delay:100ms",
                    "hx-select": "#name-errors",
                    "hx-target": "#name-errors",
                    "hx-swap": "innerHTML",
                }
            ),
            "short_description": forms.TextInput(attrs={"class": global_utils.text_field_class_names}),
            "full_description": forms.Textarea(
                attrs={
                    "class": global_utils.text_field_class_names,
                }
            ),
            "website": forms.URLInput(
                attrs={
                    "class": global_utils.text_field_class_names,
                }
            ),
            "detail_url": forms.URLInput(
                attrs={
                    "class": global_utils.text_field_class_names,
                    "placeholder": "",
                }
            ),
            "video_url": forms.URLInput(
                attrs={
                    "class": global_utils.text_field_class_names,
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
                    "class": global_utils.text_field_class_names,
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
                    "class": (
                        "block w-full pl-2 rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset"
                        " ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600"
                        " sm:text-sm sm:leading-6"
                    ),
                    "hx-post": reverse_lazy("create-organisation"),
                    "hx-trigger": "input",
                    "hx-target": "#organisation-name-errors",
                    "hx-select": "#organisation-name-errors",
                    "hx-indicator": "#ind-name",
                }
            ),
            "username": forms.TextInput(
                attrs={
                    "class": (
                        "block w-full pl-2 rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset"
                        " ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600"
                        " sm:text-sm sm:leading-6"
                    ),
                    "hx-post": reverse_lazy("create-organisation"),
                    "hx-trigger": "input",
                    "hx-target": "#organisation-username-errors",
                    "hx-select": "#organisation-username-errors",
                    "hx-indicator": "#ind-username",
                }
            ),
            "photo": forms.FileInput(
                attrs={
                    "class": (
                        "rounded-md bg-white px-2.5 py-1.5 text-sm font-semibold text-gray-900 shadow-sm ring-1"
                        " ring-inset ring-gray-300 hover:bg-gray-50"
                    ),
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

        if Organisation.objects.filter(username=username) or Person.objects.filter(user__username=username):
            raise ValidationError(_("This username is already taken."))

        return username


class ChallengeForm(forms.ModelForm):
    class_names = (
        "block w-full rounded-md border-0 p-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300"
        " placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["reward_type"].help_text = "Liquid points can be redeemed for money, Non-Liquid points cannot."

        for key, field in self.fields.items():
            attributes = {"class": self.class_names}
            if key in ["title", "description"]:
                attributes["cols"] = 40
                attributes["rows"] = 2
            if key != "reward_type":
                field.widget.attrs.update(**attributes)

    class Meta:
        model = Challenge
        fields = ["title", "description", "reward_type", "priority", "status", "product_area", "initiative"]

        widgets = {
            "reward_type": forms.RadioSelect(
                attrs={"class": "h-4 w-4 border-gray-300 text-indigo-600 focus:ring-indigo-600"}
            ),
        }


class BountyForm(forms.ModelForm):
    skill = forms.CharField(widget=forms.HiddenInput(attrs={"id": "skill_id"}))
    expertise_ids = forms.CharField(widget=forms.HiddenInput(attrs={"id": "expertise_ids"}))

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
        fields = ["title", "description", "points", "status", "is_active"]

        widgets = {
            "points": forms.NumberInput(attrs={"class": global_utils.text_field_class_names}),
            "status": forms.Select(attrs={"class": global_utils.text_field_class_names, "id": "id_bounty_status"}),
        }
        help_texts = {"is_active": "Display this bounty under the challenge that is created for."}
        labels = {
            "is_active": "Is Active",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for key, field in self.fields.items():
            attributes = {
                "class": global_utils.text_field_class_names,
                "placeholder": global_utils.placeholder(key),
            }
            if key in ["description"]:
                attributes["cols"] = 40
                attributes["rows"] = 2

            if key not in ["status", "points"]:
                field.widget.attrs.update(**attributes)


BountyFormset = modelformset_factory(
    Bounty,
    form=BountyForm,
    fields=("title", "description", "points", "status", "is_active"),
    extra=0,
    can_delete=True,
)


class InitiativeForm(forms.ModelForm):
    product = forms.ModelChoiceField(
        empty_label="Select a product",
        queryset=Product.objects.all(),
        widget=forms.Select(
            attrs={
                "class": (
                    "block w-full rounded-md border-0 p-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300"
                    " focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
                ),
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        self.slug = kwargs.pop("slug", None)
        super().__init__(*args, **kwargs)

        if self.slug:
            queryset = Product.objects.filter(slug=self.slug)
            self.fields["product"].queryset = Product.objects.filter(slug=self.slug)
            self.fields["product"].initial = queryset.first()

    class Meta:
        model = Initiative
        fields = "__all__"
        exclude = ["product", "video_url"]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": (
                        "pt-2 px-4 pb-3 w-full text-sm text-black border border-solid border-[#D9D9D9]"
                        " focus:outline-none rounded-sm"
                    ),
                    "placeholder": "Initiative Name",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": (
                        "pt-2 px-4 pb-3 min-h-[104px] w-full text-sm text-black border border-solid border-[#D9D9D9]"
                        " focus:outline-none rounded-sm"
                    ),
                    "placeholder": "Describe your initiative in detail",
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": (
                        "block w-full rounded-md border-0 p-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300"
                        " focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
                    ),
                },
                choices=Initiative.InitiativeStatus.choices,
            ),
        }


class ProductAreaForm(forms.ModelForm):
    class Meta:
        model = ProductArea
        fields = [
            "id",
            "name",
            "video_link",
            "video_name",
            "video_duration",
            "description",
        ]

        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Enter name here"}),
            "video_link": forms.TextInput(attrs={"placeholder": "Enter video link here"}),
            "video_name": forms.TextInput(attrs={"placeholder": "Enter video video_name here"}),
            "video_duration": forms.TextInput(attrs={"placeholder": "Enter video video_name here, E.x 7:20"}),
            "description": forms.Textarea(attrs={"placeholder": "Enter description here", "columns": 2}),
        }

    def __init__(self, *args, **kwargs):
        can_modify_product = kwargs.pop("can_modify_product", False)
        super(ProductAreaForm, self).__init__(*args, **kwargs)

        class_names = (
            "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none"
            " focus:shadow-outline"
        )
        for key, field in self.fields.items():
            field.widget.attrs.update({"class": class_names})
            field.widget.attrs["readonly"] = not can_modify_product


class ProductAreaForm1(forms.ModelForm):
    """TODO Merge this form to ProductAreaForm if we can"""

    root = forms.ModelChoiceField(
        required=False,
        empty_label="Select a product area",
        queryset=ProductArea.objects.all(),
        widget=forms.Select(
            attrs={
                "class": (
                    "block w-full rounded-md border-0 p-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300"
                    " focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
                ),
            }
        ),
        help_text="If you want to create a root product area, you can left this field empty.",
    )

    CHOICES = [
        ("1", "Add root"),
        ("2", "Add sibling"),
        ("3", "Add children"),
    ]

    creation_method = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=CHOICES,
    )

    # def __init__(self, *args, **kwargs):
    #     self.slug = kwargs.pop("slug", None)
    #     super().__init__(*args, **kwargs)

    #     if self.slug:
    #         product = Product.objects.get(slug=self.slug)
    #         self.fields["root"].queryset = Capability.objects.filter(product=product)

    class Meta:
        model = ProductArea
        fields = ["name", "description"]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": (
                        "pt-2 px-4 pb-3 w-full text-sm text-black border border-solid border-[#D9D9D9]"
                        " focus:outline-none rounded-sm"
                    ),
                    "placeholder": "Initiative Name",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": (
                        "pt-2 px-4 pb-3 min-h-[104px] w-full text-sm text-black border border-solid border-[#D9D9D9]"
                        " focus:outline-none rounded-sm"
                    ),
                    "placeholder": "Describe your initiative in detail",
                }
            ),
        }


class ContributorAgreementTemplateForm(forms.ModelForm):
    product = forms.ModelChoiceField(
        empty_label="Select a product",
        queryset=Product.objects.all(),
        widget=forms.Select(
            attrs={
                "class": (
                    "block w-full rounded-md border-0 p-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300"
                    " focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
                )
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        self.slug = kwargs.pop("slug", None)
        super().__init__(*args, **kwargs)

        if self.slug:
            queryset = Product.objects.filter(slug=self.slug)
            self.fields["product"].queryset = Product.objects.filter(slug=self.slug)
            self.fields["product"].initial = queryset.first()

    class Meta:
        model = ProductContributorAgreementTemplate
        fields = "__all__"
        exclude = ["created_by"]

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": (
                        "block w-full rounded-md border-0 p-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300"
                        " focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
                    )
                }
            ),
            "effective_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": (
                        "pt-2 px-4 pb-3 min-h-[104px] w-full text-sm text-black border border-solid border-[#D9D9D9]"
                        " focus:outline-none rounded-sm"
                    ),
                    "placeholder": "Select effective date",
                }
            ),
            "content": TinyMCE(
                attrs={
                    "class": (
                        "pt-2 px-4 pb-3 w-full text-sm text-black border border-solid border-[#D9D9D9]"
                        " focus:outline-none rounded-sm"
                    ),
                    "placeholder": "Agreement content",
                    "cols": 80,
                    "rows": 50,
                }
            ),
        }


class ProductRoleAssignmentForm(forms.ModelForm):
    class Meta:
        model = ProductRoleAssignment
        fields = ["person", "role"]
        widgets = {
            "role": forms.Select(
                attrs={
                    "class": (
                        "block w-full rounded-md border-0 p-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300"
                        " focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
                    ),
                },
                choices=ProductRoleAssignment.ProductRoles.choices,
            ),
        }
