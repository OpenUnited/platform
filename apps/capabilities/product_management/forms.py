import json
from datetime import date

from django import forms
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.forms import modelformset_factory
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from tinymce.widgets import TinyMCE

from apps.capabilities.commerce.models import Organisation
from apps.capabilities.security.models import ProductRoleAssignment
from apps.capabilities.talent.models import BountyClaim, Person
from apps.utility import utils as global_utils
from apps.capabilities.security.services import RoleService

from .models import Bounty, Bug, Challenge, Idea, Initiative, Product, ProductArea, ProductContributorAgreementTemplate, FileAttachment


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
    class Meta:
        model = Challenge
        fields = ['title', 'description', 'status', 'priority']


class BountyForm(forms.ModelForm):
    MIN_POINTS = 1
    MAX_POINTS = 1000

    skill = forms.CharField(
        widget=forms.HiddenInput(attrs={"id": "%(prefix)s_skill_id"}))
    expertise_ids = forms.CharField(
        widget=forms.HiddenInput(attrs={"id": "%(prefix)s_expertise_ids"}),
        required=False)

    class Meta:
        model = Bounty
        fields = ["title", "description", "points"]

        widgets = {
            "points": forms.NumberInput(attrs={"class": global_utils.text_field_class_names}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key, field in self.fields.items():
            attributes = {
                "class": global_utils.text_field_class_names,
                "placeholder": global_utils.placeholder(key),
            }
            if key == "description":
                attributes["cols"] = 40
                attributes["rows"] = 2

            if key != "points":
                field.widget.attrs.update(**attributes)

    def clean_points(self):
        points = self.cleaned_data['points']
        if points < self.MIN_POINTS or points > self.MAX_POINTS:
            raise ValidationError(f"Points must be between {self.MIN_POINTS} and {self.MAX_POINTS}")
        return points


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


class ProductForm(forms.ModelForm):
    make_me_owner = forms.BooleanField(
        required=False,
        initial=True,
        label='Make me the owner of this product'
    )
    video_url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6',
            'placeholder': 'https://youtube.com/...'
        })
    )
    detail_url = forms.URLField(
        label="Product URL",
        help_text="The public URL where users can view this product",
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'block w-full flex-1 border-0 bg-transparent py-1.5 pl-1 text-gray-900 placeholder:text-gray-400 focus:ring-0 sm:text-sm sm:leading-6'
        })
    )

    class Meta:
        model = Product
        fields = [
            'name',
            'short_description',
            'full_description',
            'website',
            'organisation',
            'make_me_owner',
            'video_url',
            'detail_url',
            'photo',
            'visibility'
        ]
        
        widgets = {
            'name': forms.TextInput(
                attrs={
                    'class': (
                        'block w-full rounded-md border-0 p-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300'
                        ' focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6'
                    ),
                    'placeholder': 'Product Name'
                }
            ),
            # ... other widget definitions remain the same ...
        }

    def __init__(self, *args, person=None, **kwargs):
        self.person = person
        super().__init__(*args, **kwargs)
        
        # Initialize form fields
        if self.person and not self.instance.pk:
            self.fields['make_me_owner'].initial = True

    def clean(self):
        cleaned_data = super().clean()
        # Either organization or make_me_owner must be set
        if not cleaned_data.get('organisation') and not cleaned_data.get('make_me_owner'):
            raise ValidationError("Either organization or make_me_owner must be specified")
        return cleaned_data

AttachmentFormSet = modelformset_factory(
    FileAttachment,
    fields=('file',),
    extra=1,
    can_delete=True
)
