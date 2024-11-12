"""
Forms for the challenge authoring flow.

This module provides form classes that handle data validation and cleaning
for the challenge authoring process. Forms are decoupled from models and 
work through the service layer.

Form Structure:
1. ChallengeAuthoringForm - Main challenge details
2. BountyAuthoringForm - Individual bounty creation

The forms handle:
- Field validation
- Data cleaning
- Initial data population
- Dynamic field choices based on product context
"""

from django import forms
from apps.common.utils import BaseModelForm
from apps.capabilities.product_management.models import Challenge, Initiative
from .services import ChallengeAuthoringService

class ChallengeAuthoringForm(BaseModelForm):
    """Form for challenge creation."""
    
    title = forms.CharField(max_length=ChallengeAuthoringService.MAX_TITLE_LENGTH)
    description = forms.CharField(widget=forms.HiddenInput())
    initiative = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="Select Initiative"
    )
    status = forms.ChoiceField(
        choices=Challenge.ChallengeStatus.choices,
        initial=Challenge.ChallengeStatus.DRAFT
    )
    priority = forms.ChoiceField(
        choices=Challenge.ChallengePriority.choices,
        initial=Challenge.ChallengePriority.HIGH
    )

    class Meta:
        model = Challenge
        fields = ['title', 'description', 'initiative', 'status', 'priority']

    def __init__(self, *args, product=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and product:
            self.service = ChallengeAuthoringService(user, product.slug)
            self.fields['initiative'].queryset = self.service.get_initiatives_for_product(product)
            
            # Remove any existing widget attributes for priority
            self.fields['priority'].widget.attrs = {}
        else:
            self.fields['initiative'].queryset = Initiative.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        success, errors = self.service.validate_challenge_data(cleaned_data, [])
        if not success:
            raise forms.ValidationError(errors)
        return cleaned_data


class BountyAuthoringForm(BaseModelForm):
    """Form for bounty creation within the challenge authoring flow."""
    
    title = forms.CharField(max_length=255)
    description = forms.CharField(widget=forms.Textarea)
    points = forms.IntegerField(min_value=1)
    skill = forms.ModelChoiceField(
        queryset=None,  # Set in __init__
        widget=forms.Select(attrs={"class": "skill-select"})
    )
    expertise_ids = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('expertise_ids'):
            raise forms.ValidationError("At least one expertise must be selected")
        return cleaned_data
