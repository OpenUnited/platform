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
from utils.forms import BaseModelForm

class ChallengeAuthoringForm(BaseModelForm):
    """
    Form for the challenge details step.
    
    This form handles the initial challenge creation step, including
    basic information, configuration, and optional settings.
    
    Fields:
        title: Challenge title (required)
        description: Full description (required)
        short_description: Brief summary (optional)
        status: Challenge status (required)
        priority: Challenge priority (required)
        reward_type: Liquid/Non-liquid points (required)
        initiative: Related initiative (optional)
        product_area: Related product area (optional)
        video_url: YouTube/Vimeo URL (optional)
    """
    
    title = forms.CharField(
        max_length=255,
        help_text="The main title of your challenge"
    )
    description = forms.CharField(
        widget=forms.Textarea,
        help_text="Detailed description of what needs to be done"
    )
    short_description = forms.CharField(
        max_length=140,
        required=False,
        help_text="A brief summary of the challenge (optional)"
    )
    status = forms.ChoiceField(
        choices=[
            ('DRAFT', 'Draft'),
            ('ACTIVE', 'Active'),
            ('COMPLETED', 'Completed'),
            ('ARCHIVED', 'Archived')
        ]
    )
    priority = forms.ChoiceField(
        choices=[
            ('HIGH', 'High'),
            ('MEDIUM', 'Medium'),
            ('LOW', 'Low')
        ]
    )
    reward_type = forms.ChoiceField(
        choices=[
            ('LIQUID', 'Liquid'),
            ('NON_LIQUID', 'Non-Liquid')
        ],
        widget=forms.RadioSelect()
    )
    initiative = forms.ModelChoiceField(
        queryset=None,  # Set in __init__
        required=False
    )
    product_area = forms.ModelChoiceField(
        queryset=None,  # Set in __init__
        required=False
    )
    video_url = forms.URLField(required=False)

    def __init__(self, *args, product=None, **kwargs):
        """
        Initialize the form with product context for related fields.

        Args:
            product: Product instance for filtering related choices
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
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
