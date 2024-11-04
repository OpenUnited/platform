"""
Services for the product management portal.

This module contains business logic for the portal features, including product management,
bounty handling, work review, and user management.
"""

from typing import Dict, List, Optional, Any
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied

from apps.capabilities.product_management.models import (
    Product,
    ProductContributorAgreementTemplate,
    Bounty,
    Challenge,
)
from apps.capabilities.talent.models import Person, BountyClaim, BountyDeliveryAttempt
from apps.capabilities.security.services import RoleService


class PortalError(Exception):
    """Base exception for portal errors."""
    pass


class PortalBaseService:
    """Base service with common functionality."""
    
    def check_product_access(self, person: Person, product: Product, required_role: str) -> None:
        """Check if person has required access to product."""
        if not RoleService.has_product_role(person, product, required_role):
            raise PortalError(f"User does not have {required_role} access to this product")
    
    def get_product_or_404(self, slug: str) -> Product:
        """Get product by slug or raise 404."""
        return get_object_or_404(Product, slug=slug)


class PortalService(PortalBaseService):
    """Main service for portal operations."""
    
    def get_user_context(self, person: Optional[Person]) -> Dict[str, Any]:
        """Get basic context for user including products they have access to."""
        if not person:
            raise PortalError("No person associated with user")
            
        return {
            "products": RoleService.get_user_products(person=person),
            "managed_products": RoleService.get_managed_products(person=person),
            "person": person,
        }

    def get_product_detail_context(self, slug: str, person: Person, tab: str = 'challenges') -> Dict[str, Any]:
        """Get context data for product detail view."""
        product = self.get_product_or_404(slug)
        self.check_product_access(person, product, 'Member')
        
        context = {
            'product': product,
            'current_product': product,
            'active_tab': tab,
        }
        
        # Add tab-specific context
        tab_handlers = {
            'challenges': self._get_challenges_context,
            'bounty-claims': self._get_bounty_claims_context,
            'work-review': self._get_work_review_context,
        }
        
        handler = tab_handlers.get(tab)
        if handler:
            context.update(handler(product))
        
        return context

    def _get_challenges_context(self, product: Product) -> Dict[str, Any]:
        return {
            'challenges': Challenge.objects.filter(product=product).order_by('-created_at')
        }

    def _get_bounty_claims_context(self, product: Product) -> Dict[str, Any]:
        return {
            'bounty_claims': BountyClaim.objects.filter(
                bounty__challenge__product=product,
                status=BountyClaim.Status.REQUESTED
            )
        }

    def get_user_products(self, person: Person) -> List[Product]:
        """Get all products accessible to user."""
        return RoleService.get_user_products(person=person)
    
    def get_product_settings_context(self, slug: str, person: Person) -> Dict[str, Any]:
        """Get context for product settings."""
        product = self.get_product_or_404(slug)
        self.check_product_access(person, product, 'Admin')
        return {
            'product': product,
            'current_product': product,
        }
    
    def get_product_bounties_context(self, slug: str, person: Person) -> Dict[str, Any]:
        """Get context for product bounties list."""
        product = self.get_product_or_404(slug)
        self.check_product_access(person, product, 'Member')
        return {
            'product': product,
            'current_product': product,
            'bounties': Bounty.objects.filter(challenge__product=product)
        }

    def get_products_context(self, person: Person) -> Dict[str, Any]:
        """Get context for products list view."""
        return {
            'products': RoleService.get_user_products(person=person),
            'managed_products': RoleService.get_managed_products(person=person),
        }

    def handle_bounty_claim_action(self, slug: str, bounty_id: int, claim_id: int, 
                                 action: str, person: Person) -> None:
        """Handle bounty claim accept/reject actions."""
        product = self.get_product_or_404(slug)
        bounty = get_object_or_404(Bounty, pk=bounty_id, challenge__product=product)
        claim = get_object_or_404(BountyClaim, pk=claim_id, bounty=bounty)
        
        self.check_product_access(person, product, 'Manager')
        
        if action == 'accept':
            claim.status = BountyClaim.Status.GRANTED
        elif action == 'reject':
            claim.status = BountyClaim.Status.REJECTED
        else:
            raise PortalError("Invalid action")
            
        claim.save()


class BountyService:
    """
    Service for managing bounties and bounty claims.
    """
    
    def handle_claim_action(self, claim_id: int, action: str) -> BountyClaim:
        """Handle accepting, rejecting, or cancelling a bounty claim."""
        claim = get_object_or_404(BountyClaim, pk=claim_id)
        
        if action == "accept":
            self._accept_claim(claim)
        elif action == "reject":
            self._reject_claim(claim)
        elif action == "cancel":
            self._cancel_claim(claim)
        else:
            raise ValueError(f"Invalid action: {action}")
            
        return claim

    def _accept_claim(self, claim: BountyClaim) -> None:
        """Accept a bounty claim and reject other claims."""
        claim.status = BountyClaim.Status.GRANTED
        claim.save()
        
        # Reject other claims for this challenge
        BountyClaim.objects.filter(
            bounty__challenge=claim.bounty.challenge
        ).exclude(
            pk=claim.pk
        ).update(status=BountyClaim.Status.REJECTED)

    def _reject_claim(self, claim: BountyClaim) -> None:
        """Reject a bounty claim."""
        claim.status = BountyClaim.Status.REJECTED
        claim.save()

    def _cancel_claim(self, claim: BountyClaim) -> None:
        """Cancel a bounty claim if it's in REQUESTED status."""
        if claim.status != BountyClaim.Status.REQUESTED:
            raise ValueError("Only active claims can be cancelled.")
        
        claim.status = BountyClaim.Status.CANCELLED
        claim.save()

    def get_user_bounty_claims(self, person: Person) -> List[BountyClaim]:
        """Get active bounty claims for a user."""
        return BountyClaim.objects.filter(
            person=person,
            status__in=[
                BountyClaim.Status.GRANTED,
                BountyClaim.Status.REQUESTED,
            ],
        )


class ProductUserService:
    """
    Service for managing product users and roles.
    """

    def get_product_users_context(self, product_slug: str) -> Dict[str, Any]:
        """Get context for product users management view."""
        product = get_object_or_404(Product, slug=product_slug)
        return {
            "product": product,
            "product_users": RoleService.get_product_members(product=product)
        }

    def assign_user_role(self, product_slug: str, person: Person, role: str) -> None:
        """Assign a role to a user for a product."""
        product = get_object_or_404(Product, slug=product_slug)
        RoleService.assign_product_role(
            person=person,
            product=product,
            role=role
        )

    def get_user_role_assignment(self, product_slug: str, user_id: int):
        """Get user's role assignment for a product."""
        product = get_object_or_404(Product, slug=product_slug)
        return RoleService.get_user_product_role(
            person_id=user_id,
            product=product
        )

    def update_user_role(self, product_slug: str, user_id: int, role: str) -> None:
        """Update a user's role for a product."""
        product = get_object_or_404(Product, slug=product_slug)
        RoleService.update_product_role(
            person_id=user_id,
            product=product,
            role=role
        )


class ChallengeService(PortalBaseService):
    """Service for managing product challenges."""
    
    def get_challenges_context(self, slug: str, person: Person) -> Dict[str, Any]:
        """Get context for challenges management."""
        product = self.get_product_or_404(slug)
        self.check_product_access(person, product, 'Member')
        
        return {
            'product': product,
            'current_product': product,
            'challenges': Challenge.objects.filter(product=product).order_by('-created_at'),
            'can_manage': RoleService.has_product_role(person, product, 'Manager')
        }


class BountyDeliveryReviewService(PortalBaseService):
    """Service for reviewing bounty delivery attempts."""
    
    def get_review_context(self, slug: str, person: Person) -> Dict[str, Any]:
        """Get context for work review."""
        product = self.get_product_or_404(slug)
        self.check_product_access(person, product, 'Manager')
        
        return {
            'product': product,
            'current_product': product,
            'delivery_attempts': BountyDeliveryAttempt.objects.filter(
                bounty_claim__bounty__challenge__product=product,
                status=BountyDeliveryAttempt.Status.SUBMITTED
            ).select_related('bounty_claim', 'bounty_claim__bounty', 'bounty_claim__person')
        }
    
    def review_delivery_attempt(
        self, 
        attempt_id: int, 
        approved: bool, 
        feedback: str,
        reviewer: Person
    ) -> None:
        """Review a delivery attempt."""
        attempt = get_object_or_404(BountyDeliveryAttempt, pk=attempt_id)
        product = attempt.bounty_claim.bounty.challenge.product
        
        self.check_product_access(reviewer, product, 'Manager')
        
        attempt.status = (
            BountyDeliveryAttempt.Status.APPROVED if approved 
            else BountyDeliveryAttempt.Status.REJECTED
        )
        attempt.feedback = feedback
        attempt.reviewed_by = reviewer
        attempt.save()


class AgreementTemplateService(PortalBaseService):
    """Service for managing product agreement templates."""
    
    def get_templates_context(self, slug: str, person: Person) -> Dict[str, Any]:
        """Get context for agreement templates."""
        product = self.get_product_or_404(slug)
        self.check_product_access(person, product, 'Admin')
        
        return {
            'product': product,
            'current_product': product,
            'templates': ProductContributorAgreementTemplate.objects.filter(product=product),
            'can_manage': True  # Admin access already checked
        }
    
    def create_template(self, slug: str, person: Person, data: Dict[str, Any]) -> ProductContributorAgreementTemplate:
        """Create a new agreement template."""
        product = self.get_product_or_404(slug)
        self.check_product_access(person, product, 'Admin')
        
        template = ProductContributorAgreementTemplate(
            product=product,
            title=data['title'],
            content=data['content'],
            created_by=person
        )
        template.save()
        return template
    
    def update_template(self, slug: str, template_id: int, person: Person, data: Dict[str, Any]) -> ProductContributorAgreementTemplate:
        """Update an existing agreement template."""
        product = self.get_product_or_404(slug)
        self.check_product_access(person, product, 'Admin')
        
        template = get_object_or_404(
            ProductContributorAgreementTemplate,
            id=template_id,
            product=product
        )
        
        template.title = data['title']
        template.content = data['content']
        template.updated_by = person
        template.save()
        return template
    
    def delete_template(self, slug: str, template_id: int, person: Person) -> None:
        """Delete an agreement template."""
        product = self.get_product_or_404(slug)
        self.check_product_access(person, product, 'Admin')
        
        template = get_object_or_404(
            ProductContributorAgreementTemplate,
            id=template_id,
            product=product
        )
        template.delete()