"""
Services for the product management portal.

This module contains business logic for the portal features, including product management,
bounty handling, work review, and user management.
"""

from typing import Dict, List, Optional, Any
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
import logging
from django.db.models import Count

from apps.capabilities.commerce.models import Organisation
from apps.capabilities.product_management.models import (
    Product,
    ProductContributorAgreementTemplate,
    Bounty,
    Challenge,
)
from apps.capabilities.talent.models import Person, BountyClaim, BountyDeliveryAttempt
from apps.capabilities.security.services import RoleService

logger = logging.getLogger(__name__)


class PortalError(Exception):
    """Base exception for portal errors."""
    pass


class PortalBaseService:
    """Base service with common functionality."""
    
    def check_product_access(self, person: Person, product: Product, required_role: str = None) -> None:
        """Check if person has required access to product."""
        if required_role:
            if not RoleService.has_product_role(person, product, required_role):
                logger.warning(f"Access denied: {person} does not have {required_role} role for {product}")
                raise PermissionDenied(f"User does not have {required_role} access to this product")
        else:
            if not RoleService.has_product_access(person, product):
                logger.warning(f"Access denied: {person} does not have access to {product}")
                raise PermissionDenied("User does not have access to this product")
    
    def get_product_or_404(self, slug: str) -> Product:
        """Get product by slug or raise 404."""
        return get_object_or_404(Product, slug=slug)

    def get_base_product_context(self, product: Product, person: Optional[Person] = None) -> Dict[str, Any]:
        """Get common context data for product views."""
        context = {
            'product': product,
            'current_product': product,
            'current_product_slug': product.slug,
        }
        if person:
            context['can_manage'] = RoleService.has_product_role(person, product, 'Manager')
            context['can_admin'] = RoleService.has_product_role(person, product, 'Admin')
        return context

    def get_product_summary(self, slug: str, person: Person) -> Dict[str, Any]:
        """Get summary data for product overview page."""
        product = self.get_product_or_404(slug)
        self.check_product_access(person, product)
        
        context = self.get_base_product_context(product, person)
        
        # Add summary statistics
        context.update({
            'active_challenges_count': Challenge.objects.filter(
                product=product,
                status='active'
            ).count(),
            'open_bounties_count': Bounty.objects.filter(
                challenge__product=product,
                status='open'
            ).count(),
            'active_contributors_count': RoleService.get_product_members(product).count(),
        })
        
        return context

    def get_current_organisation(self, request):
        """Get the current organisation from session or default to first available."""
        current_org_id = request.session.get('current_organisation_id')
        logger.info(f"Getting current org - session org_id: {current_org_id}")
        
        if not current_org_id:
            logger.warning("No current_organisation_id in session")
            return None
            
        try:
            org = Organisation.objects.get(id=current_org_id)
            logger.info(f"Found current org: {org.id} - {org.name}")
            return org
        except Organisation.DoesNotExist:
            logger.error(f"Organisation {current_org_id} not found")
            return None


class PortalService(PortalBaseService):
    """Main service for portal operations."""
    
    def get_user_context(self, person: Optional[Person]) -> Dict[str, Any]:
        """Get basic context for user including products and organizations they have access to."""
        if not person:
            raise PortalError("No person associated with user")
            
        # Get current organization from session if available
        current_org_id = self.request.session.get('current_organisation_id') if hasattr(self, 'request') else None
        
        # Get all organizations the user has access to with their roles
        user_orgs = RoleService.get_person_organisations_with_roles(person)
        
        # If we have a current_org_id, find it in the user's orgs
        current_org = None
        if current_org_id:
            for org_assignment in user_orgs:
                if org_assignment.organisation.id == current_org_id:
                    current_org = org_assignment.organisation
                    break
        
        # If no current org found, use the first available
        if not current_org and user_orgs:
            current_org = user_orgs[0].organisation
            
        # Get products for the current organization
        org_products = []
        if current_org:
            org_products = Product.objects.filter(
                organisation=current_org
            ).order_by('name')
            
        return {
            "person": person,
            "current_organisation": current_org,
            "user_organisations": user_orgs,
            "organisation_products": org_products,
            "products": RoleService.get_user_products(person=person),
            "managed_products": RoleService.get_managed_products(person=person),
            "can_manage_org": current_org and RoleService.is_organisation_manager(
                person, 
                current_org
            ) if current_org else False
        }

    def switch_organisation(self, person: Person, org_id: int) -> Organisation:
        """Handle organization switching."""
        organisation = get_object_or_404(Organisation, id=org_id)
        
        # Verify user has access to this organisation
        has_access = RoleService.has_organisation_role(
            person, 
            organisation
        )
        
        if not has_access:
            raise PermissionDenied("User does not have access to this organisation")
        
        return organisation

    def get_product_detail_context(self, slug: str, person: Person, tab: str = 'challenges') -> Dict[str, Any]:
        """Get context data for product detail view."""
        product = self.get_product_or_404(slug)
        self.check_product_access(person, product)
        
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
        self.check_product_access(person, product)
        return {
            'product': product,
            'current_product': product,
        }
    
    def get_product_bounties_context(self, slug: str, person: Person) -> Dict[str, Any]:
        """Get context for product bounties list."""
        product = self.get_product_or_404(slug)
        self.check_product_access(person, product)
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
        
        self.check_product_access(person, product)
        
        if action == 'accept':
            claim.status = BountyClaim.Status.GRANTED
        elif action == 'reject':
            claim.status = BountyClaim.Status.REJECTED
        else:
            raise PortalError("Invalid action")
            
        claim.save()

    def _get_work_review_context(self, product: Product) -> Dict[str, Any]:
        """Get context data for work review tab."""
        return {
            'delivery_attempts': BountyDeliveryAttempt.objects.filter(
                bounty_claim__bounty__challenge__product=product,
                status=BountyDeliveryAttempt.Status.SUBMITTED
            ).select_related('bounty_claim', 'bounty_claim__bounty', 'bounty_claim__person')
        }

    def get_dashboard_context(self, person: Person) -> Dict[str, Any]:
        """Get context data for user dashboard."""
        if not person:
            raise PortalError("No person associated with user")
            
        context = {
            "person": person,
            "page_title": "Dashboard",
        }
        
        # Get personal products
        context["personal_products"] = Product.objects.filter(person=person)
        
        # Get current organisation and its products if in org context
        if hasattr(person, 'request') and person.request.session.get('current_organisation_id'):
            org_id = person.request.session['current_organisation_id']
            current_org = Organisation.objects.filter(id=org_id).first()
            
            if current_org:
                # Get organisation-specific data
                context["organisation_products"] = Product.objects.filter(
                    organisation=current_org
                ).select_related('organisation')
                context["current_organisation"] = current_org
        
        # Get bounty claims regardless of context
        context["active_bounty_claims"] = BountyClaim.objects.filter(
            person=person,
            status__in=[
                BountyClaim.Status.GRANTED,
                BountyClaim.Status.REQUESTED
            ]
        ).select_related('bounty', 'bounty__challenge', 'bounty__challenge__product')
        
        return context

    def get_product_summary_context(self, slug: str, person: Person) -> Dict[str, Any]:
        """Get context data for product summary view."""
        product = self.get_product_or_404(slug)
        self.check_product_access(person, product)
        
        context = self.get_base_product_context(product, person)
        
        # Add summary statistics
        context.update({
            'active_challenges_count': Challenge.objects.filter(
                product=product, 
                status='active'
            ).count(),
            'open_bounties_count': Bounty.objects.filter(
                challenge__product=product,
                status='open'
            ).count(),
            'pending_reviews_count': BountyDeliveryAttempt.objects.filter(
                bounty_claim__bounty__challenge__product=product,
                status=BountyDeliveryAttempt.Status.SUBMITTED
            ).count(),
            'recent_activity': self._get_recent_product_activity(product)
        })
        
        return context
        
    def _get_recent_product_activity(self, product: Product) -> List[Dict[str, Any]]:
        """Get recent activity for a product."""
        # Aggregate recent activity from various models
        activities = []
        
        # Get recent challenges
        challenges = Challenge.objects.filter(
            product=product
        ).order_by('-created_at')[:5]
        
        # Get recent bounty claims
        claims = BountyClaim.objects.filter(
            bounty__challenge__product=product
        ).order_by('-created_at')[:5]
        
        # Get recent delivery attempts
        attempts = BountyDeliveryAttempt.objects.filter(
            bounty_claim__bounty__challenge__product=product
        ).order_by('-created_at')[:5]
        
        # Combine and sort activities
        for challenge in challenges:
            activities.append({
                'type': 'challenge',
                'date': challenge.created_at,
                'title': challenge.title,
                'status': challenge.status,
                'url': f'/portal/products/{product.slug}/challenges/{challenge.slug}/'
            })
        
        for claim in claims:
            activities.append({
                'type': 'claim',
                'date': claim.created_at,
                'title': claim.bounty.title,
                'person': claim.person.name,
                'status': claim.status,
                'url': f'/portal/products/{product.slug}/bounties/{claim.bounty.id}/'
            })
        
        for attempt in attempts:
            activities.append({
                'type': 'delivery',
                'date': attempt.created_at,
                'title': attempt.bounty_claim.bounty.title,
                'person': attempt.bounty_claim.person.name,
                'status': attempt.status,
                'url': f'/portal/products/{product.slug}/review/{attempt.id}/'
            })
        
        return activities


class BountyService:
    """
    Service for managing bounties and bounty claims.
    """
    
    def handle_claim_action(self, claim_id: int, action: str) -> BountyClaim:
        """Handle accepting, rejecting, or cancelling a bounty claim."""
        claim = get_object_or_404(BountyClaim, pk=claim_id)
        
        try:
            if action == "accept":
                self._accept_claim(claim)
            elif action == "reject":
                self._reject_claim(claim)
            elif action == "cancel":
                self._cancel_claim(claim)
            else:
                raise PortalError(f"Invalid action: {action}")
        except ValueError as e:
            raise PortalError(str(e))
            
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
        logger.info(
            "User role updated - Product: %s, User: %s, Role: %s",
            product_slug, user_id, role
        )


class ChallengeService(PortalBaseService):
    """Service for managing product challenges."""
    
    def get_challenges_context(self, slug: str, person: Person) -> Dict[str, Any]:
        """Get context for challenges management."""
        product = self.get_product_or_404(slug)
        self.check_product_access(person, product)
        
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
        self.check_product_access(person, product)
        
        return {
            'product': product,
            'current_product': product,
            'delivery_attempts': BountyDeliveryAttempt.objects.filter(
                bounty_claim__bounty__challenge__product=product,
                kind=BountyDeliveryAttempt.SubmissionType.NEW
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
        
        self.check_product_access(reviewer, product)
        
        attempt.status = (
            BountyDeliveryAttempt.Status.APPROVED if approved 
            else BountyDeliveryAttempt.SubmissionType.REJECTED
        )
        attempt.feedback = feedback
        attempt.reviewed_by = reviewer
        attempt.save()


class AgreementTemplateService(PortalBaseService):
    """Service for managing product agreement templates."""
    
    def get_templates_context(self, slug: str, person: Person) -> Dict[str, Any]:
        """Get context for agreement templates."""
        product = self.get_product_or_404(slug)
        self.check_product_access(person, product)
        
        return {
            'product': product,
            'current_product': product,
            'templates': ProductContributorAgreementTemplate.objects.filter(product=product),
            'can_manage': True  # Admin access already checked
        }
    
    def create_template(self, slug: str, person: Person, data: Dict[str, Any]) -> ProductContributorAgreementTemplate:
        """Create a new agreement template."""
        product = self.get_product_or_404(slug)
        self.check_product_access(person, product)
        
        template = ProductContributorAgreementTemplate(
            product=product,
            title=data['title'],
            content=data['content'],
            created_by=person,
            effective_date=data.get('effective_date')
        )
        template.save()
        return template
    
    def update_template(self, slug: str, template_id: int, person: Person, data: Dict[str, Any]) -> ProductContributorAgreementTemplate:
        """Update an existing agreement template."""
        product = self.get_product_or_404(slug)
        self.check_product_access(person, product)
        
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
        self.check_product_access(person, product)
        
        template = get_object_or_404(
            ProductContributorAgreementTemplate,
            id=template_id,
            product=product
        )
        template.delete()
