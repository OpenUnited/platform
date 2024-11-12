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
from django.http import Http404
from django.shortcuts import get_object_or_404

from apps.capabilities.product_management.models import Challenge, Bounty, Product, FileAttachment
from apps.capabilities.talent.models import Skill, Expertise
from apps.capabilities.security.services import RoleService

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
        MAX_POINTS_PER_BOUNTY (int): Maximum points per bounty (1000)
        MAX_TOTAL_POINTS (int): Maximum total points across all bounties (1000)
    
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
    MAX_POINTS_PER_BOUNTY = 1000
    MAX_TOTAL_POINTS = 1000

    def __init__(self, user, product_slug):
        if not hasattr(user, 'person') or not user.person:
            raise PermissionDenied("User must have an associated person")
            
        self.user = user
        self.product = get_object_or_404(Product, slug=product_slug)
        self.role_service = RoleService()
        
        # Check if user is product manager
        if not self.role_service.is_product_manager(self.user.person, self.product):
            raise PermissionDenied("Must be product manager")

    def create_challenge(self, challenge_data, bounties_data):
        errors = {}
        
        # Validate challenge data
        if not challenge_data.get('title'):
            errors['title'] = ['Title is required']
        if not challenge_data.get('description'):
            errors['description'] = ['Description is required']
        if challenge_data.get('status') not in ['draft', 'published']:
            errors['status'] = ['Invalid status']
            
        # Validate bounties
        if bounties_data:
            bounty_errors = []
            total_points = sum(b.get('points', 0) for b in bounties_data)
            
            if total_points > 1000:
                bounty_errors.append('Total points cannot exceed 1000')
                
            for bounty in bounties_data:
                if not Skill.objects.filter(id=bounty.get('skill_id')).exists():
                    bounty_errors.append(f"Invalid skill ID: {bounty.get('skill_id')}")
                    
            if bounty_errors:
                errors['bounties'] = bounty_errors
                
        if errors:
            return False, None, errors
            
        try:
            with transaction.atomic():
                challenge = Challenge.objects.create(**challenge_data)
                for bounty_data in bounties_data:
                    expertise_ids = bounty_data.pop('expertise_ids', [])
                    bounty = Bounty.objects.create(
                        challenge=challenge,
                        **bounty_data
                    )
                    bounty.expertise.set(expertise_ids)
                return True, challenge, None
        except Exception as e:
            return False, None, {'error': str(e)}

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
        seen_titles = set()  # Initialize the set to track duplicate titles

        if len(bounties_data) > self.MAX_BOUNTIES:
            errors.append(f'Maximum of {self.MAX_BOUNTIES} bounties allowed per challenge')
            
        total_points = sum(bounty.get('points', 0) for bounty in bounties_data)
        if total_points > self.MAX_TOTAL_POINTS:
            errors.append(f'Total points across all bounties cannot exceed {self.MAX_TOTAL_POINTS}')
            
        for i, bounty in enumerate(bounties_data):
            # Required fields
            if not bounty.get('title'):
                errors.append(f"Bounty {i+1}: Title is required")
            if not bounty.get('description'):
                errors.append(f"Bounty {i+1}: Description is required")
            if not bounty.get('skill'):
                errors.append(f"Bounty {i+1}: Skill is required")
                
            # Title validation
            title = bounty.get('title', '')
            if title in seen_titles:
                errors.append(f"Bounty {i+1}: Duplicate bounty title")
            seen_titles.add(title)
            
            if len(title) > self.MAX_TITLE_LENGTH:
                errors.append(f"Bounty {i+1}: Title must be less than {self.MAX_TITLE_LENGTH} characters")
                
            # Points validation
            points = bounty.get('points', 0)
            if points <= 0 or points > self.MAX_POINTS_PER_BOUNTY:
                errors.append(f'Points must be between 1 and {self.MAX_POINTS_PER_BOUNTY}')
            total_points += points
            
            # Expertise validation
            expertise_ids = bounty.get('expertise_ids', '')
            if isinstance(expertise_ids, str):
                expertise_ids = expertise_ids.split(',') if expertise_ids else []
            if not expertise_ids:
                errors.append(f"Bounty {i+1}: At least one expertise must be selected")
            else:
                # Validate expertise belongs to selected skill
                skill_id = bounty.get('skill')
                if skill_id:
                    valid_expertise = Expertise.objects.filter(
                        skill_id=skill_id,
                        id__in=expertise_ids
                    ).count()
                    if valid_expertise != len(expertise_ids):
                        errors.append(f"Bounty {i+1}: Invalid expertise selection for chosen skill")
        
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
        skills = Skill.objects.filter(
            selectable=True  # Only include selectable skills
        ).select_related('parent')
        
        skill_tree = []
        skill_dict = {}
        
        # First pass: create all skill objects with their basic data
        for skill in skills:
            skill_data = {
                'id': skill.id,
                'name': skill.name,
                'children': [],
                'selectable': skill.selectable,
                'parent_id': skill.parent_id if skill.parent else None
            }
            skill_dict[skill.id] = skill_data
            
            # Add root nodes directly to the tree
            if not skill.parent:
                skill_tree.append(skill_data)
        
        # Second pass: establish parent-child relationships
        for skill in skills:
            if skill.parent_id and skill.parent_id in skill_dict:
                parent_data = skill_dict[skill.parent_id]
                parent_data['children'].append(skill_dict[skill.id])
        
        return skill_tree

    def get_expertise_for_skill(self, skill_id):
        expertise_items = Expertise.objects.filter(
            skill_id=skill_id
        ).select_related('parent')
        
        return [
            {
                'id': item.id,
                'name': item.name,
                'parent_id': item.parent_id
            }
            for item in expertise_items
        ]

    def get_skills_list(self):
        return [
            {'id': skill.id, 'name': skill.name}
            for skill in Skill.objects.all()
        ]

    def _get_product(self, product_slug: str) -> Product:
        """
        Get product by slug and verify user has permission to manage it.
        
        Args:
            product_slug (str): The product's slug identifier
            
        Returns:
            Product: The product instance if found and user has permission
            
        Raises:
            PermissionDenied: If user lacks product management permission
            Http404: If product not found
        """
        try:
            product = Product.objects.get(slug=product_slug)
            if not self.role_service.is_product_manager(self.user, product):
                raise PermissionDenied("User is not a product manager")
            return product
        except Product.DoesNotExist:
            raise Http404("Product not found")

    def create_bounty(self, challenge: Challenge, bounty_data: Dict) -> Tuple[bool, Optional[str]]:
        """Create a bounty with proper expertise handling"""
        try:
            expertise_ids = bounty_data.pop('expertise_ids', [])
            bounty = Bounty.objects.create(
                challenge=challenge,
                **bounty_data
            )
            if expertise_ids:
                bounty.expertise.set(expertise_ids)
            return True, None
        except Exception as e:
            logger.error(f"Error creating bounty: {str(e)}")
            raise

    def validate_challenge_data(self, challenge_data, bounties_data):
        errors = {}
        
        if not challenge_data.get('title'):
            errors['title'] = ['Title is required']
        if not challenge_data.get('description'):
            errors['description'] = ['Description is required']
        if challenge_data.get('status') not in ['draft', 'published']:
            errors['status'] = ['Invalid status']
            
        if len(bounties_data) > 10:
            errors['bounties'] = ['Maximum 10 bounties allowed']
            
        total_points = sum(b.get('points', 0) for b in bounties_data)
        if total_points > 1000:
            errors['bounties'] = ['Total points cannot exceed 1000']
            
        return not bool(errors), errors

    def get_file_attachments(self, challenge_id=None):
        """Get file attachments for a challenge"""
        if challenge_id:
            return FileAttachment.objects.filter(challenge_id=challenge_id)
        return FileAttachment.objects.none()

    def save_file_attachments(self, challenge, attachments):
        """Save file attachments for a challenge"""
        saved_attachments = []
        for attachment in attachments:
            file_attachment = FileAttachment(
                challenge=challenge,
                file=attachment
            )
            file_attachment.save()
            saved_attachments.append(file_attachment)
        return saved_attachments
