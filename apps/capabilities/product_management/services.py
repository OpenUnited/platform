import logging
from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Dict, List, Optional, Tuple
from django.db.models import Q, QuerySet

from apps.capabilities.talent.models import Person, Expertise
from apps.capabilities.security.services import RoleService
from .models import Bounty, Challenge, Product
from . import forms

logger = logging.getLogger(__name__)

class ChallengeCreationService:
    def __init__(self, challenge_data: Dict, bounties_data: List[Dict], user):
        self.challenge_data = challenge_data
        self.bounties_data = bounties_data
        self.user = user
        self.logger = logging.getLogger(__name__)

    def validate_data(self) -> Optional[List[str]]:
        errors = []
        # Add validation logic
        return errors if errors else None

    def process_submission(self) -> Tuple[bool, Optional[str]]:
        try:
            if errors := self.validate_data():
                return False, str(errors)

            with transaction.atomic():
                challenge = self._create_challenge()
                if self.bounties_data:
                    self._create_bounties(challenge)
                self.logger.info(f"Challenge {challenge.id} created successfully")
                return True, None
        except Exception as e:
            self.logger.error(f"Error processing challenge submission: {e}")
            return False, str(e)

    def _create_challenge(self):
        return Challenge.objects.create(
            **self.challenge_data,
            created_by=self.user.person
        )

    def _create_bounties(self, challenge):
        for bounty_data in self.bounties_data:
            try:
                if isinstance(bounty_data, str):
                    import json
                    bounty_data = json.loads(bounty_data)
                
                bounty_data.pop('reward_type', None)  # Remove if exists since it's inherited
                
                # Create bounty directly
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

class ProductService:
    @staticmethod
    def convert_youtube_link_to_embed(url: str):
        if url:
            return url.replace("watch?v=", "embed/")
    
    @staticmethod
    def get_visible_products(user) -> QuerySet[Product]:
        """
        Get all products that should be visible to the user based on:
        1. For anonymous users: only GLOBAL products
        2. For authenticated users:
           - GLOBAL products
           - ORG_ONLY products where user is a member
           - RESTRICTED products where user has explicit access
           - Products owned by the user
        
        Args:
            user: The authenticated user or None
            
        Returns:
            QuerySet of visible Product objects
        """
        if not user or not user.is_authenticated:
            # Anonymous users can only see GLOBAL products
            return (Product.objects
                   .filter(visibility=Product.Visibility.GLOBAL)
                   .order_by('-created_at')
                   .select_related('person', 'organisation'))
        
        # For authenticated users, get all products they have access to
        user_products = RoleService.get_user_products(user.person)
        
        return (
            Product.objects
            .filter(
                Q(visibility=Product.Visibility.GLOBAL) |
                Q(id__in=user_products.values_list('id', flat=True))
            )
            .distinct()
            .order_by('-created_at')
            .select_related('person', 'organisation')
        )

    @staticmethod
    def has_product_visibility_access(user, product: Product) -> bool:
        """
        Check if a user should be able to see a specific product based on:
        1. Anonymous users can only see GLOBAL products
        2. Authenticated users can see:
           - GLOBAL products
           - Products they have access to through RoleService
        
        Args:
            user: The authenticated user or None
            product: The product to check visibility for
            
        Returns:
            bool indicating if the user can see this product
        """
        # Anonymous users can only see GLOBAL products
        if not user or not user.is_authenticated:
            return product.visibility == Product.Visibility.GLOBAL
            
        # Check if product is in user's accessible products
        user_products = RoleService.get_user_products(user.person)
        return (product.visibility == Product.Visibility.GLOBAL or 
                user_products.filter(id=product.id).exists())
