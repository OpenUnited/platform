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
from apps.capabilities.product_management.models import Challenge, Bounty
from apps.capabilities.talent.models import Skill
from apps.capabilities.talent.services import SkillService
from .services import ChallengeAuthoringService
import logging
from django.forms import ModelForm, modelformset_factory
from apps.capabilities.product_management.models import FileAttachment

logger = logging.getLogger(__name__)

class ChallengeAuthoringForm(BaseModelForm):
    """Form for challenge creation."""
    
    title = forms.CharField(max_length=ChallengeAuthoringService.MAX_TITLE_LENGTH)
    description = forms.CharField(widget=forms.HiddenInput())
    priority = forms.ChoiceField(
        choices=Challenge.ChallengePriority.choices,
        initial=Challenge.ChallengePriority.HIGH,
        required=True
    )

    class Meta:
        model = Challenge
        fields = ['title', 'description', 'priority']

    def __init__(self, *args, product=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and product:
            self.service = ChallengeAuthoringService(user, product.slug)
            # Remove initiative queryset setup

    def clean(self):
        cleaned_data = super().clean()
        
        # Log the cleaning process
        logger.debug(f"Cleaning form data: {cleaned_data}")
        
        # Only check bounties if there are no other errors
        if not self.errors:
            bounties = self.request.session.get('pending_bounties', []) if hasattr(self, 'request') else []
            logger.debug(f"Checking bounties in clean: {bounties}")
            
            if not bounties:
                logger.debug("No bounties found, adding error")
                self.add_error(None, 'At least one bounty is required')
            
        return cleaned_data


class BountyAuthoringForm(BaseModelForm):
    """Form for bounty creation within the challenge authoring flow."""
    
    skill = forms.ChoiceField(
        required=True,
        choices=[],
        label="Skill *"
    )
    title = forms.CharField(
        max_length=255,
        label="Title *"
    )
    description = forms.CharField(
        widget=forms.Textarea,
        label="Description *"
    )
    points = forms.IntegerField(
        min_value=1,
        label="Points *"
    )

    class Meta:
        model = Bounty
        fields = ['skill', 'title', 'description', 'points']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Fetch all active skills
        skills = Skill.objects.filter(active=True).order_by('parent_id', 'name')
        
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
        
        # Include all choices
        self.fields['skill'].choices = [('', 'Select a skill')] + choices

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('expertise_ids'):
            raise forms.ValidationError("At least one expertise must be selected")
        return cleaned_data

class AttachmentForm(ModelForm):
    class Meta:
        model = FileAttachment
        fields = ['file']

AttachmentFormSet = modelformset_factory(
    FileAttachment,
    form=AttachmentForm,
    fields=['file'],
    extra=1,
    can_delete=True,
    max_num=10
)
