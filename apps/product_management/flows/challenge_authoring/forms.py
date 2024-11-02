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
from apps.product_management.models import Challenge

class ChallengeAuthoringForm(BaseModelForm):
    """Form for challenge creation within the challenge authoring flow."""
    
    title = forms.CharField(max_length=255)
    description = forms.CharField(widget=forms.Textarea)
    initiative = forms.ModelChoiceField(
        queryset=None,  # Set in __init__
        required=False
    )
    product_area = forms.ModelChoiceField(
        queryset=None,  # Set in __init__
        required=False
    )
    video_url = forms.URLField(required=False)

    class Meta:
        model = Challenge
        fields = ['title', 'description', 'initiative', 'product_area', 'video_url']

    def __init__(self, *args, product=None, **kwargs):
        super().__init__(*args, **kwargs)
        if product:
            self.fields['initiative'].queryset = product.initiatives.all()
            self.fields['product_area'].queryset = product.product_areas.all()


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
