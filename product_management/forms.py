from datetime import date
from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


from talent.models import BountyClaim
from .models import Idea


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
