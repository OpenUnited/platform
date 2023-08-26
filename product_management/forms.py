from datetime import date
from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


from talent.models import BountyClaim


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
