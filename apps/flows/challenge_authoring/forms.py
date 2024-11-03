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
from apps.capabilities.product_management.models import Challenge, ProductArea, Initiative

class ChallengeAuthoringForm(BaseModelForm):
    """Form for challenge creation within the challenge authoring flow."""
    
    title = forms.CharField(max_length=255)
    description = forms.CharField(widget=forms.Textarea)
    initiative = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="Select Initiative"
    )
    product_area = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="Select Product Area"
    )
    video_url = forms.URLField(required=False)
    status = forms.ChoiceField(
        choices=Challenge.ChallengeStatus.choices,
        initial=Challenge.ChallengeStatus.DRAFT,
        required=True
    )
    priority = forms.ChoiceField(
        choices=Challenge.ChallengePriority.choices,
        initial=Challenge.ChallengePriority.HIGH,
        required=True
    )

    class Meta:
        model = Challenge
        fields = ['title', 'description', 'initiative', 'product_area', 'video_url', 'status', 'priority']

    def __init__(self, *args, **kwargs):
        product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)
        
        if product:
            # Set the queryset for initiatives
            self.fields['initiative'].queryset = Initiative.objects.filter(product=product)
            
            # Set the queryset for product areas - filter through product_tree
            self.fields['product_area'].queryset = ProductArea.objects.filter(
                product_tree__product=product
            )
        else:
            self.fields['initiative'].queryset = Initiative.objects.none()
            self.fields['product_area'].queryset = ProductArea.objects.none()

    class Media:
        js = [
            'js/ChallengeFlowCore.js',
            'js/ChallengeFlowBounties.js',
            'js/ChallengeFlow.js',
            'js/BountyModal.js'
        ]
        css = {
            'all': ['css/bounty_modal.css']
        }


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
