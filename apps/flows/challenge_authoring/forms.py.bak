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
from apps.capabilities.product_management.models import Challenge, Initiative, Bounty
from apps.capabilities.talent.models import Skill
from apps.capabilities.talent.services import SkillService
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
    points = forms.IntegerField(min_value=1)
    skill = forms.ChoiceField(
        required=True,
        choices=[]
    )

    class Meta:
        model = Bounty
        fields = ['title', 'points', 'skill']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Fetch all active skills
        skills = Skill.objects.filter(active=True).order_by('parent_id', 'name')
        
        # Debug: Log the number of skills fetched
        print(f"DEBUG: Number of skills fetched: {skills.count()}")
        
        # Build hierarchical choices
        def build_choices(skills, parent=None, level=0):
            choices = []
            for skill in skills:
                if skill.parent_id == parent:
                    indent = '--' * level
                    # Add non-selectable parents as headers
                    if not skill.selectable:
                        choices.append((None, f"{indent} {skill.name}"))
                    # Recursively add children
                    choices.extend(build_choices(skills, skill.id, level + 1))
                    # Add selectable skills
                    if skill.selectable:
                        choices.append((skill.id, f"{indent} {skill.name}"))
            return choices
        
        choices = build_choices(skills)
        print(f"DEBUG: Number of choices prepared: {len(choices)}")
        
        # Include all choices, but disable non-selectable ones
        self.fields['skill'].choices = [('', 'Select a skill')] + choices

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('expertise_ids'):
            raise forms.ValidationError("At least one expertise must be selected")
        return cleaned_data
