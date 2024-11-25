import logging
from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Dict, List, Optional, Tuple
from django.db.models import Q, QuerySet
from django.http import HttpResponse
from itertools import groupby
from operator import attrgetter
from urllib.parse import urlparse
from abc import ABC, abstractmethod
from django.conf import settings
import httpx
import time
import json

from apps.capabilities.talent.models import Person, Expertise
from apps.capabilities.security.services import RoleService
from apps.common import utils
from .models import Bounty, Challenge, Product, Idea, Bug, IdeaVote, ProductContributorAgreementTemplate, ProductArea, Initiative
from apps.capabilities.commerce.models import Organisation
from . import forms
from apps.capabilities.security.models import ProductRoleAssignment
from apps.common.exceptions import ServiceException, InvalidInputError, ResourceNotFoundError
from apps.portal.services.ai_services import LLMService
from apps.event_hub.services.factory import get_event_bus

logger = logging.getLogger(__name__)

class ChallengeCreationService:
    def __init__(self, challenge_data: Dict, bounties_data: List[Dict], user):
        self.challenge_data = challenge_data
        self.bounties_data = bounties_data
        self.user = user
        self.logger = logging.getLogger(__name__)

    def validate_data(self) -> None:
        """
        Validate challenge and bounty data
        
        Raises:
            InvalidInputError: If data is invalid
        """
        if not self.challenge_data.get('title'):
            raise InvalidInputError("Challenge title is required")
            
        if not self.challenge_data.get('product'):
            raise InvalidInputError("Product is required")
            
        for bounty_data in self.bounties_data:
            if not bounty_data.get('title'):
                raise InvalidInputError("Bounty title is required")
            if bounty_data.get('points', 0) <= 0:
                raise InvalidInputError("Bounty points must be positive")

    @transaction.atomic
    def process_submission(self) -> tuple[bool, Optional[str]]:
        """
        Process challenge submission with atomic transaction

        Returns:
            Tuple of (success, error_message)
        Raises:
            InvalidInputError: If input data is invalid
        """
        try:
            self.validate_data()  # Let this raise InvalidInputError

            challenge = Challenge.objects.create(
                **self.challenge_data,
                created_by=self.user.person
            )

            for bounty_data in self.bounties_data:
                bounty = Bounty.objects.create(
                    **bounty_data,
                    challenge=challenge,
                    status=Bounty.BountyStatus.AVAILABLE
                )

                if expertise_ids := bounty_data.get('expertise_ids'):
                    if isinstance(expertise_ids, str):
                        expertise_ids = expertise_ids.split(',')
                    bounty.expertise.add(*Expertise.objects.filter(id__in=expertise_ids))

            logger.info(f"Challenge {challenge.id} created successfully")
            return True, None

        except InvalidInputError:
            # Re-raise InvalidInputError instead of catching it
            raise
        except Exception as e:
            logger.error(f"Error creating challenge: {e}")
            return False, f"Failed to create challenge: {str(e)}"

class ProductService:
    @staticmethod
    def convert_youtube_link_to_embed(url: str) -> str:
        """Convert YouTube URL to embed format"""
        if not url:
            return url
            
        # Strict validation for YouTube URLs using domain check
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        if domain not in ['youtube.com', 'www.youtube.com', 'youtu.be', 'www.youtu.be']:
            logger.debug(f"Invalid URL domain: {domain}")
            raise InvalidInputError("Not a valid YouTube URL")
            
        try:
            if 'youtube.com' in domain:
                if 'watch?v=' not in url:
                    logger.debug(f"Invalid YouTube URL format: {url}")
                    raise InvalidInputError("Invalid YouTube URL format")
                video_id = url.split('v=')[1].split('&')[0]
            else:  # youtu.be
                if 'youtu.be/' not in url:
                    logger.debug(f"Invalid YouTube short URL format: {url}")
                    raise InvalidInputError("Invalid YouTube URL format")
                video_id = url.split('youtu.be/')[1].split('?')[0]
                
            if not video_id:
                logger.debug("No video ID found")
                raise InvalidInputError("Could not find YouTube video ID")
                
            return f"https://www.youtube.com/embed/{video_id}"
        except (IndexError, KeyError) as e:
            logger.debug(f"Failed to parse URL: {e}")
            raise InvalidInputError("Could not parse YouTube URL")

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

class IdeaService:
    @staticmethod
    def create_idea(form_data: Dict, person: Person, product: Product) -> Tuple[bool, Optional[str], Optional[Idea]]:
        """Create a new idea for a product"""
        try:
            idea = Idea.objects.create(
                person=person,
                product=product,
                **form_data
            )
            return True, None, idea
        except Exception as e:
            logger.error(f"Error creating idea: {e}")
            return False, str(e), None

    @staticmethod
    def update_idea(idea: Idea, form_data: Dict) -> Tuple[bool, Optional[str]]:
        """Update an existing idea"""
        try:
            for key, value in form_data.items():
                setattr(idea, key, value)
            idea.save()
            return True, None
        except Exception as e:
            logger.error(f"Error updating idea: {e}")
            return False, str(e)

    @staticmethod
    def get_idea(pk: int) -> Optional[Idea]:
        """Get an idea by primary key"""
        try:
            return Idea.objects.get(pk=pk)
        except Idea.DoesNotExist:
            return None

    @staticmethod
    def get_product_ideas(product: Product) -> QuerySet[Idea]:
        """Get all ideas for a product"""
        return Idea.objects.filter(product=product)

    @staticmethod
    def toggle_vote(idea: Idea, user) -> Tuple[bool, Optional[str], int]:
        """Toggle a vote for an idea"""
        try:
            if IdeaVote.objects.filter(idea=idea, voter=user).exists():
                IdeaVote.objects.get(idea=idea, voter=user).delete()
            else:
                IdeaVote.objects.create(idea=idea, voter=user)
            return True, None, IdeaVote.objects.filter(idea=idea).count()
        except Exception as e:
            logger.error(f"Error toggling vote: {e}")
            return False, str(e), 0

    @staticmethod
    def can_modify_idea(idea: Idea, person: Person) -> bool:
        """Check if a person can modify an idea"""
        return idea.person == person


class BugService:
    @staticmethod
    def create_bug(form_data: Dict, person: Person, product: Product) -> Tuple[bool, Optional[str], Optional[Bug]]:
        """Create a new bug for a product"""
        try:
            bug = Bug.objects.create(
                person=person,
                product=product,
                **form_data
            )
            return True, None, bug
        except Exception as e:
            logger.error(f"Error creating bug: {e}")
            return False, str(e), None

    @staticmethod
    def update_bug(bug: Bug, form_data: Dict) -> Tuple[bool, Optional[str]]:
        """Update an existing bug"""
        try:
            for key, value in form_data.items():
                setattr(bug, key, value)
            bug.save()
            return True, None
        except Exception as e:
            logger.error(f"Error updating bug: {e}")
            return False, str(e)

    @staticmethod
    def get_bug(pk: int) -> Optional[Bug]:
        """Get a bug by primary key"""
        try:
            return Bug.objects.get(pk=pk)
        except Bug.DoesNotExist:
            return None

    @staticmethod
    def get_product_bugs(product: Product) -> QuerySet[Bug]:
        """Get all bugs for a product"""
        return Bug.objects.filter(product=product)

    @staticmethod
    def can_modify_bug(bug: Bug, person: Person) -> bool:
        """Check if a person can modify a bug"""
        return bug.person == person


class IdeasAndBugsService:
    @staticmethod
    def get_product_ideas_and_bugs(product: Product) -> Tuple[QuerySet[Idea], QuerySet[Bug]]:
        """Get all ideas and bugs for a product"""
        ideas = IdeaService.get_product_ideas(product)
        bugs = BugService.get_product_bugs(product)
        return ideas, bugs

class ProductManagementService:
    @staticmethod
    def create_product(form_data: dict, person: Person, organisation: Organisation = None) -> Product:
        """
        Create a product and assign the creator as admin
        
        Args:
            form_data: Cleaned form data
            person: Person creating the product
            organisation: Optional organisation to own the product
            
        Returns:
            Created Product instance
        """
        logger.info(f"Creating product - person: {person}, org: {organisation}")
        
        if not form_data.get('name'):
            raise InvalidInputError("Product name is required")
            
        try:
            product_data = form_data.copy()
            if organisation:
                product_data['organisation'] = organisation
            
            # Create the product
            product = Product.objects.create(**product_data)
            logger.info(f"Product created: {product.id} - {product.name}")
            
            # Assign creator as admin
            RoleService.assign_product_role(
                person=person,
                product=product,
                role=ProductRoleAssignment.ProductRoles.ADMIN
            )
            logger.info(f"Assigned {person} as ADMIN for product {product.id}")

            # Publish event
            event_bus = get_event_bus()
            event_bus.publish('product.created', {
                'organisation_id': product.organisation_id if product.organisation else None,
                'person_id': product.person_id if product.person else None,
                'name': product.name,
                'url': product.get_absolute_url(),
                'product_id': product.id
            })
            logger.info(f"Published product.created event for product {product.id}")
            
            return product
            
        except ValidationError as e:
            logger.error(f"Validation error creating product: {str(e)}")
            raise InvalidInputError(str(e))
        except Exception as e:
            logger.error(f"Error creating product: {str(e)}", exc_info=True)
            raise InvalidInputError(f"Failed to create product: {str(e)}")

    @staticmethod
    def update_product(product: Product, form_data: Dict) -> Tuple[bool, Optional[str]]:
        try:
            for key, value in form_data.items():
                setattr(product, key, value)
            product.save()
            return True, None
        except Exception as e:
            logger.error(f"Error updating product: {e}")
            return False, str(e)

class ContributorAgreementService:
    @staticmethod
    def create_template(form_data: Dict, person: Person) -> Tuple[bool, Optional[str], Optional[ProductContributorAgreementTemplate]]:
        try:
            template = ProductContributorAgreementTemplate.objects.create(
                **form_data,
                created_by=person
            )
            return True, None, template
        except Exception as e:
            logger.error(f"Error creating template: {e}")
            return False, str(e), None

class OrganisationService:
    @staticmethod
    def create_organisation(form_data: Dict) -> Tuple[bool, Optional[str], Optional[Organisation]]:
        try:
            org = Organisation.objects.create(**form_data)
            return True, None, org
        except Exception as e:
            logger.error(f"Error creating organisation: {e}")
            return False, str(e), None

class ProductAreaService:
    @staticmethod
    def create_area(form_data: Dict) -> Tuple[bool, Optional[str], Optional[ProductArea]]:
        try:
            area = ProductArea.add_root(**form_data)
            return True, None, area
        except Exception as e:
            logger.error(f"Error creating product area: {e}")
            return False, str(e), None

    @staticmethod
    def update_area(area: ProductArea, form_data: Dict) -> Tuple[bool, Optional[str]]:
        try:
            for key, value in form_data.items():
                setattr(area, key, value)
            area.save()
            return True, None
        except Exception as e:
            logger.error(f"Error updating product area: {e}")
            return False, str(e)

class InitiativeService:
    @classmethod
    def create_initiative(cls, form_data: dict, person) -> tuple[bool, Optional[str], Optional[Initiative]]:
        """Create a new initiative
        
        Args:
            form_data: Initiative form data
            person: Person creating the initiative
            
        Returns:
            Tuple of (success, error_message, initiative)
        """
        try:
            # Remove created_by from form_data since it's not a model field
            form_data = form_data.copy()
            if 'created_by' in form_data:
                del form_data['created_by']
                
            initiative = Initiative.objects.create(**form_data)
            logger.info(f"Initiative {initiative.id} created successfully")
            return True, None, initiative
            
        except Exception as e:
            logger.error(f"Error creating initiative: {e}")
            return False, str(e), None

    @staticmethod
    def get_product_initiatives(product: Product) -> QuerySet:
        """Get all initiatives for a specific product."""
        return Initiative.objects.filter(
            product=product
        ).select_related(
            'product'  # only include fields that exist in the model
        ).order_by('-created_at')

class ChallengeService:
    @staticmethod
    def get_product_challenges(product: Product) -> QuerySet:
        """Get challenges for a specific product with related data."""
        return Challenge.objects.filter(
            product=product
        ).select_related(
            'product_area',
            'created_by'
        ).prefetch_related(
            'bounty_set'
        )

class ProductTreeService:
    @staticmethod
    def get_product_tree_data(product: Product) -> List:
        """Get tree data for a product."""
        product_tree = product.product_trees.first()
        if not product_tree:
            return []
            
        product_areas = ProductArea.get_root_nodes().filter(product_tree=product_tree)
        return [utils.serialize_tree(node) for node in product_areas]

class ProductPeopleService:
    @staticmethod
    def get_grouped_product_roles(product: Product) -> dict:
        """Get all role assignments for a specific product, grouped by role."""
        assignments = ProductRoleAssignment.objects.filter(
            product=product
        ).select_related(
            'person',
            'product'
        ).order_by('role')

        # Convert to dictionary with role as key and list of assignments as value
        grouped = {}
        for assignment in assignments:
            if assignment.role not in grouped:
                grouped[assignment.role] = []
            grouped[assignment.role].append(assignment)
            
        return grouped.items()  # Return as list of tuples (role, assignments)

class BountyService:
    @staticmethod
    def get_visible_bounties(user) -> QuerySet:
        """Get all bounties visible to the user."""
        visible_products = ProductService.get_visible_products(user)
        return (Bounty.objects
                .filter(challenge__product__in=visible_products)
                .select_related('challenge', 'challenge__product')
                .order_by('-created_at'))

    @staticmethod
    def get_product_bounties(product_slug: str) -> QuerySet:
        """Get bounties for a specific product."""
        return (Bounty.objects
                .filter(challenge__product__slug=product_slug)
                .select_related('challenge', 'challenge__product')
                .order_by('-created_at'))

class ProductContentService:
    """Handles ideas, bugs and other product content"""
    
    @staticmethod
    def get_product_content(product: Product) -> Dict:
        """Get all content for a product"""
        return {
            'ideas': IdeaService.get_product_ideas(product),
            'bugs': BugService.get_product_bugs(product),
            'initiatives': InitiativeService.get_product_initiatives(product),
            'challenges': ChallengeService.get_product_challenges(product)
        }
        
    @staticmethod
    def get_content_stats(product: Product) -> Dict:
        """Get content statistics for a product"""
        return {
            'idea_count': Idea.objects.filter(product=product).count(),
            'bug_count': Bug.objects.filter(product=product).count(),
            'initiative_count': Initiative.objects.filter(product=product).count(),
            'challenge_count': Challenge.objects.filter(product=product).count()
        }

