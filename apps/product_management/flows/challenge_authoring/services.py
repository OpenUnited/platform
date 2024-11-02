"""
Service layer for the challenge authoring flow.

This module provides the business logic for creating challenges and bounties
within a product context. It handles validation, data processing, and ensures
business rules are followed.

Validation Rules:
1. Challenge Rules:
   - Title length and format
   - Description minimum length
   - Valid status and priority values
   - Video URL format (YouTube/Vimeo only)
   - Product context validation

2. Bounty Rules:
   - Maximum 10 bounties per challenge
   - Points between 1-1000
   - No duplicate titles
   - Expertise must match selected skill

3. Cross-validation:
   - Active challenges require bounties
   - Consistent reward types
"""

from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.validators import URLValidator
from typing import Dict, List, Optional, Tuple
import logging
import re
from django.db.models import QuerySet
from apps.talent.models import Skill, Expertise

from apps.product_management.models import Challenge, Bounty, Expertise, Product
from apps.security.services import RoleService

logger = logging.getLogger(__name__)

class ChallengeAuthoringService:
    """
    Service for managing the challenge creation process.
    
    This service enforces business rules, handles validation, and manages
    the creation of challenges and bounties within a product context.
    
    Attributes:
        MAX_TITLE_LENGTH (int): Maximum length for titles (255)
        MAX_SHORT_DESC_LENGTH (int): Maximum length for short descriptions (140)
        MIN_POINTS (int): Minimum points per bounty (1)
        MAX_POINTS (int): Maximum points per bounty (1000)
        MAX_BOUNTIES (int): Maximum bounties per challenge (10)
    
    Example:
        service = ChallengeAuthoringService(user, 'product-slug')
        
        # Validate data
        errors = service.validate_data(challenge_data, bounties_data)
        if errors:
            handle_errors(errors)
            
        # Create challenge
        success, challenge, errors = service.create_challenge(
            challenge_data,
            bounties_data
        )
    """

    MAX_TITLE_LENGTH = 255
    MAX_SHORT_DESC_LENGTH = 140
    MIN_POINTS = 1
    MAX_POINTS = 1000
    MAX_BOUNTIES = 10

    def __init__(self, user, product_slug: str = None):
        """
        Initialize the service with a user and product context.

        Args:
            user: The authenticated user creating the challenge
            product_slug (str): Slug identifier for the product
        """
        self.user = user
        if product_slug:
            self.product = self._get_product(product_slug)
            self.role_service = RoleService()
            if not self._can_create_challenges():
                raise PermissionDenied

    def _can_create_challenges(self) -> bool:
        """Check if user has permission to create challenges"""
        if not hasattr(self.user, 'person'):
            return False
            
        return self.role_service.is_product_manager(
            person=self.user.person,
            product=self.product
        )

    def create_challenge(self, challenge_data: Dict, bounties_data: List[Dict]) -> Tuple[bool, Optional[Challenge], List[str]]:
        """
        Creates a challenge with its associated bounties.

        Args:
            challenge_data (Dict): Challenge fields and values
            bounties_data (List[Dict]): List of bounty data dictionaries

        Returns:
            Tuple containing:
            - bool: Success status
            - Optional[Challenge]: Created challenge or None
            - List[str]: Error messages if any
        """
        try:
            with transaction.atomic():
                # Create the challenge
                challenge = Challenge.objects.create(
                    **challenge_data,
                    created_by=self.user.person,
                    product=self.product
                )
                
                # Create associated bounties
                if bounties_data:
                    self._create_bounties(challenge, bounties_data)
                
                logger.info(
                    f"Challenge {challenge.id} created successfully by user {self.user.id}"
                )
                return True, challenge, []

        except ValidationError as e:
            logger.error(f"Validation error in challenge creation: {str(e)}")
            return False, None, e.messages

        except Exception as e:
            logger.error(f"Error in challenge creation: {str(e)}")
            return False, None, [str(e)]

    def _create_bounties(self, challenge: Challenge, bounties_data: List[Dict]):
        """Creates bounties associated with the challenge."""
        for bounty_data in bounties_data:
            try:
                # Handle JSON string data if needed
                if isinstance(bounty_data, str):
                    import json
                    bounty_data = json.loads(bounty_data)
                
                # Remove reward_type if exists since it's inherited
                bounty_data.pop('reward_type', None)
                
                # Create bounty
                bounty = Bounty.objects.create(
                    **bounty_data,
                    challenge=challenge,
                    status=Bounty.BountyStatus.AVAILABLE
                )
                
                # Handle expertise if provided
                if expertise_ids := bounty_data.get('expertise_ids'):
                    if isinstance(expertise_ids, str):
                        expertise_ids = expertise_ids.split(',')
                    bounty.expertise.add(*Expertise.objects.filter(id__in=expertise_ids))
                
            except Exception as e:
                logger.error(f"Error creating bounty: {e}")
                raise

    def get_challenge_choices(self):
        """Get choices for challenge form dropdowns."""
        return {
            'reward_types': Challenge.REWARD_TYPE_CHOICES,
            'priorities': Challenge.PRIORITY_CHOICES,
            'statuses': Challenge.STATUS_CHOICES,
        }

    def validate_data(self, challenge_data: Dict, bounties_data: List[Dict]) -> List[str]:
        """Validates challenge and bounty data before creation."""
        errors = []
        
        # Challenge validation
        errors.extend(self._validate_challenge(challenge_data))
        
        # Bounties validation
        errors.extend(self._validate_bounties(bounties_data))
        
        # Cross-validation
        errors.extend(self._validate_challenge_bounty_relationship(challenge_data, bounties_data))
        
        return errors

    def _validate_challenge(self, data: Dict) -> List[str]:
        """Validates challenge-specific data."""
        errors = []
        
        # Required fields
        if not data.get('title'):
            errors.append("Challenge title is required")
        if not data.get('description'):
            errors.append("Challenge description is required")
            
        # Title validation
        title = data.get('title', '')
        if len(title) > self.MAX_TITLE_LENGTH:
            errors.append(f"Title must be less than {self.MAX_TITLE_LENGTH} characters")
        if title and not re.match(r'^[\w\s\-.,!?()]+$', title):
            errors.append("Title contains invalid characters")
            
        # Description validation
        description = data.get('description', '')
        if len(description.strip()) < 50:
            errors.append("Description must be at least 50 characters long")
            
        # Short description validation
        short_description = data.get('short_description', '')
        if short_description and len(short_description) > self.MAX_SHORT_DESC_LENGTH:
            errors.append(f"Short description must be less than {self.MAX_SHORT_DESC_LENGTH} characters")
            
        # Status validation
        status = data.get('status')
        valid_statuses = ['DRAFT', 'ACTIVE', 'COMPLETED', 'ARCHIVED']
        if status not in valid_statuses:
            errors.append(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
            
        # Priority validation
        priority = data.get('priority')
        valid_priorities = ['HIGH', 'MEDIUM', 'LOW']
        if priority not in valid_priorities:
            errors.append(f"Invalid priority. Must be one of: {', '.join(valid_priorities)}")
            
        # Video URL validation
        if video_url := data.get('video_url'):
            url_validator = URLValidator()
            try:
                url_validator(video_url)
                # Optional: Add specific video platform validation
                if not any(platform in video_url for platform in ['youtube.com', 'vimeo.com']):
                    errors.append("Video URL must be from YouTube or Vimeo")
            except ValidationError:
                errors.append("Invalid video URL format")
                
        # Initiative validation
        if initiative_id := data.get('initiative'):
            if not self.product.initiatives.filter(id=initiative_id).exists():
                errors.append("Selected initiative does not belong to this product")
                
        # Product area validation
        if area_id := data.get('product_area'):
            if not self.product.product_areas.filter(id=area_id).exists():
                errors.append("Selected product area does not belong to this product")
        
        return errors

    def _validate_bounties(self, bounties_data: List[Dict]) -> List[str]:
        """Validates bounty-specific data."""
        errors = []
        
        # Check total number of bounties
        if len(bounties_data) > self.MAX_BOUNTIES:
            errors.append(f"Maximum of {self.MAX_BOUNTIES} bounties allowed per challenge")
            return errors
        
        total_points = 0
        seen_titles = set()
        
        for i, bounty in enumerate(bounties_data, 1):
            # Required fields
            if not bounty.get('title'):
                errors.append(f"Bounty {i}: Title is required")
            if not bounty.get('description'):
                errors.append(f"Bounty {i}: Description is required")
            if not bounty.get('skill'):
                errors.append(f"Bounty {i}: Skill is required")
                
            # Title validation
            title = bounty.get('title', '')
            if title in seen_titles:
                errors.append(f"Bounty {i}: Duplicate bounty title")
            seen_titles.add(title)
            
            if len(title) > self.MAX_TITLE_LENGTH:
                errors.append(f"Bounty {i}: Title must be less than {self.MAX_TITLE_LENGTH} characters")
                
            # Points validation
            points = bounty.get('points', 0)
            if not isinstance(points, (int, float)) or points < self.MIN_POINTS:
                errors.append(f"Bounty {i}: Points must be at least {self.MIN_POINTS}")
            if points > self.MAX_POINTS:
                errors.append(f"Bounty {i}: Points cannot exceed {self.MAX_POINTS}")
            total_points += points
            
            # Expertise validation
            expertise_ids = bounty.get('expertise_ids', '')
            if isinstance(expertise_ids, str):
                expertise_ids = expertise_ids.split(',') if expertise_ids else []
            if not expertise_ids:
                errors.append(f"Bounty {i}: At least one expertise must be selected")
            else:
                # Validate expertise belongs to selected skill
                skill_id = bounty.get('skill')
                if skill_id:
                    valid_expertise = Expertise.objects.filter(
                        skill_id=skill_id,
                        id__in=expertise_ids
                    ).count()
                    if valid_expertise != len(expertise_ids):
                        errors.append(f"Bounty {i}: Invalid expertise selection for chosen skill")
        
        return errors

    def _validate_challenge_bounty_relationship(self, challenge_data: Dict, bounties_data: List[Dict]) -> List[str]:
        """Validates relationships between challenge and its bounties."""
        errors = []
        
        # Ensure at least one bounty for active challenges
        if challenge_data.get('status') == 'ACTIVE' and not bounties_data:
            errors.append("Active challenges must have at least one bounty")
            
        # Validate reward type consistency
        reward_type = challenge_data.get('reward_type')
        if reward_type and bounties_data:
            for i, bounty in enumerate(bounties_data, 1):
                if bounty.get('reward_type') and bounty['reward_type'] != reward_type:
                    errors.append(f"Bounty {i}: Reward type must match challenge reward type")
        
        return errors

    def get_skills_tree(self) -> List[Dict]:
        """Get hierarchical skills structure for the challenge form"""
        skills = Skill.objects.all().select_related('parent')
        
        skill_tree = []
        skill_dict = {}
        
        # First pass: create all skill objects
        for skill in skills:
            skill_data = {
                'id': skill.id,
                'name': skill.name,
                'children': [],
                'selectable': skill.selectable
            }
            skill_dict[skill.id] = skill_data
            
            if not skill.parent:
                skill_tree.append(skill_data)
                
        # Second pass: establish parent-child relationships
        for skill in skills:
            if skill.parent:
                parent_data = skill_dict.get(skill.parent.id)
                if parent_data:
                    parent_data['children'].append(skill_dict[skill.id])
                    
        return skill_tree

    def get_expertise_for_skill(self, skill_id: int) -> Dict[str, List[Dict]]:
        """Get expertise options for a given skill"""
        expertises = Expertise.objects.filter(
            skill_id=skill_id,
            selectable=True
        ).select_related('parent').order_by('parent__name', 'name')
        
        expertise_categories = {}
        for expertise in expertises:
            if expertise.parent:
                category_name = expertise.parent.name
                expertise_categories.setdefault(category_name, []).append({
                    'id': expertise.id,
                    'name': expertise.name
                })
                
        return expertise_categories

    def get_skills_list(self) -> List[Dict]:
        """Get all available skills.
        
        Returns:
            List[Dict]: List of skills with their IDs and names
            Example: [
                {"id": 1, "name": "Frontend Development"},
                {"id": 2, "name": "Backend Development"}
            ]
        """
        return list(Skill.objects.values('id', 'name').order_by('name'))

    def get_expertise_for_skill(self, skill_id: int) -> List[Dict]:
        """Get expertise options for a specific skill.
        
        Args:
            skill_id: ID of the skill to get expertise for
            
        Returns:
            List[Dict]: List of expertise with their IDs, names and levels
            Example: [
                {"id": 1, "name": "React", "level": "BEGINNER"},
                {"id": 2, "name": "React", "level": "INTERMEDIATE"},
                {"id": 3, "name": "React", "level": "EXPERT"}
            ]
        """
        return list(
            Expertise.objects
            .filter(skill_id=skill_id)
            .values('id', 'name', 'level')
            .order_by('level', 'name')
        )
