from typing import Dict, List, Optional, Tuple
from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied, ObjectDoesNotExist
from django.db.models import QuerySet, Avg, Count
from django.utils.translation import gettext_lazy as _

from apps.capabilities.product_management.models import Bounty
from apps.capabilities.talent.forms import PersonProfileForm, PersonSkillFormSet
from . import utils

from .models import (
    Person, PersonSkill, Skill, Expertise, 
    Feedback, BountyClaim, BountyDeliveryAttempt
)
from apps.capabilities.security.models import ProductRoleAssignment


class ProfileService:
    @staticmethod
    def get_user_profile(username: str) -> Person:
        """Get user profile with related data"""
        return Person.objects.select_related('user').get(user__username=username)

    @staticmethod
    @transaction.atomic
    def update_profile(person: Person, profile_data: dict, skills_data: list) -> Person:
        """Update profile and associated skills"""
        # Update basic profile fields
        for key, value in profile_data.items():
            setattr(person, key, value)
        person.full_clean()
        person.save()

        # Update skills
        PersonSkill.objects.filter(person=person).delete()
        for skill_data in skills_data:
            if not skill_data.get('skill'):
                continue
            PersonSkill.objects.create(
                person=person,
                skill_id=skill_data['skill'],
                expertise_ids=skill_data.get('expertise', [])
            )
        
        return person

    @staticmethod
    def get_active_skills() -> QuerySet:
        """Get all active skills ordered by boost factor"""
        return (Skill.objects
                .filter(active=True)
                .order_by('-display_boost_factor'))

    @staticmethod
    def get_expertises_for_skill(skill_id: int) -> QuerySet:
        """Get expertise hierarchy for a given skill"""
        return (Expertise.get_roots()
                .filter(skill_id=skill_id)
                .prefetch_related('expertise_children'))

    @staticmethod
    def get_profile_context(person: Person, is_htmx: bool, request_data: dict = None) -> dict:
        """Get all context data needed for profile view"""
        context = {
            "pk": person.pk,
            "person_skill_formset": PersonSkillFormSet(
                request_data.get('POST') if request_data else None,
                request_data.get('FILES') if request_data else None,
                instance=person,
            )
        }
        
        if is_htmx:
            context.update(ProfileService._get_htmx_context(
                person, 
                request_data.get('GET', {}) if request_data else {}
            ))
        else:
            context.update(ProfileService._get_standard_context(person))
            
        return context

    @staticmethod
    def _get_htmx_context(person: Person, get_params: dict) -> dict:
        context = {}
        index = get_params.get("index")
        
        if skill_id := get_params.get(f"skills-{index}-skill"):
            expertises = ProfileService.get_expertises_for_skill(skill_id)
            context["expertises"] = expertises
        else:
            context["empty_form"] = PersonSkillFormSet().empty_form
            context["skills"] = ProfileService.get_active_skills()
        
        context["index"] = index
        return context

    @staticmethod
    def _get_standard_context(person: Person) -> dict:
        skills = ProfileService.get_active_skills()
        return {
            "form": PersonProfileForm(instance=person),
            "photo_url": person.get_photo_url(),
            "skills": skills,
            "selected_skills": skills,
            "expertises": ProfileService.get_expertises_for_skill(None)
        }


class ShowcaseService:
    @staticmethod
    def get_showcase_data(username: str, viewing_user=None) -> Dict:
        """Get all data needed for talent showcase"""
        person = ProfileService.get_user_profile(username)
        
        showcase_data = {
            'person': person,
            'person_linkedin_link': utils.get_path_from_url(person.linkedin_link, True),
            'person_twitter_link': utils.get_path_from_url(person.twitter_link, True),
            'person_skills': person.skills.all().select_related("skill"),
            'bounty_claims_completed': ShowcaseService._get_completed_claims(person),
            'bounty_claims_claimed': ShowcaseService._get_claimed_bounties(person),
            'received_feedbacks': FeedbackService.get_person_feedbacks(person),
            'can_leave_feedback': False,
        }
        
        if viewing_user and not viewing_user.is_anonymous:
            showcase_data['can_leave_feedback'] = FeedbackService.can_leave_feedback(
                viewing_user.person, 
                person
            )
            
        return showcase_data

    @staticmethod
    def _get_completed_claims(person: Person) -> QuerySet:
        return (BountyClaim.objects
            .filter(
                status=BountyClaim.Status.COMPLETED,
                person=person
            )
            .select_related('bounty__challenge', 'bounty__challenge__product'))

    @staticmethod
    def _get_claimed_bounties(person: Person) -> QuerySet:
        return (BountyClaim.objects
            .filter(
                bounty__status=Bounty.BountyStatus.CLAIMED,
                person=person
            )
            .select_related('bounty__challenge', 'bounty__challenge__product'))


class BountyDeliveryService:
    @staticmethod
    @transaction.atomic
    def create_delivery_attempt(
        person: Person,
        bounty_claim: BountyClaim,
        attempt_data: dict
    ) -> BountyDeliveryAttempt:
        """Create new delivery attempt and update bounty claim status"""
        # Create the attempt
        attempt = BountyDeliveryAttempt.objects.create(
            person=person,
            bounty_claim=bounty_claim,
            kind=BountyDeliveryAttempt.SubmissionType.NEW,
            **attempt_data
        )

        # Update claim status
        bounty_claim.status = BountyClaim.Status.CONTRIBUTED
        bounty_claim.save()

        return attempt

    @staticmethod
    def get_attempt_details(
        attempt_id: int,
        requesting_person: Person
    ) -> Tuple[BountyDeliveryAttempt, bool]:
        """Get attempt details and check if user is admin"""
        attempt = BountyDeliveryAttempt.objects.get(id=attempt_id)
        product = attempt.bounty_claim.bounty.challenge.product
        
        is_product_admin = ProductRoleAssignment.objects.filter(
            product=product,
            person=requesting_person,
            role__in=[
                ProductRoleAssignment.ProductRoles.ADMIN,
                ProductRoleAssignment.ProductRoles.MANAGER
            ]
        ).exists()

        return attempt, is_product_admin

    @staticmethod
    @transaction.atomic
    def process_attempt(
        attempt_id: int,
        action: str,
        admin_person: Person
    ) -> BountyDeliveryAttempt:
        """Process (approve/reject) delivery attempt"""
        attempt = BountyDeliveryAttempt.objects.get(id=attempt_id)
        
        # Verify admin permissions
        product = attempt.bounty_claim.bounty.challenge.product
        is_admin = ProductRoleAssignment.objects.filter(
            product=product,
            person=admin_person,
            role__in=[
                ProductRoleAssignment.ProductRoles.ADMIN,
                ProductRoleAssignment.ProductRoles.MANAGER
            ]
        ).exists()
        
        if not is_admin:
            raise PermissionDenied(_("Only product admins can process delivery attempts"))

        if action == 'approve':
            attempt.kind = BountyDeliveryAttempt.SubmissionType.APPROVED
        elif action == 'reject':
            attempt.kind = BountyDeliveryAttempt.SubmissionType.REJECTED
        else:
            raise ValidationError(_("Invalid action"))

        attempt.save()
        return attempt

    @staticmethod
    def handle_delivery_action(attempt_id: int, action_value: str, admin_person: Person) -> None:
        """Handle delivery attempt action (approve/reject)"""
        if action_value not in ["approve-bounty-claim-delivery", "reject-bounty-claim-delivery"]:
            raise ValidationError(_("Invalid action"))
            
        action = "approve" if "approve" in action_value else "reject"
        BountyDeliveryService.process_attempt(
            attempt_id=attempt_id,
            action=action,
            admin_person=admin_person
        )


class FeedbackService:
    @staticmethod
    def can_leave_feedback(provider: Person, recipient: Person) -> bool:
        """Check if provider can leave feedback for recipient"""
        if provider == recipient:
            return False
        
        # Check if feedback already exists
        existing_feedback = Feedback.objects.filter(
            provider=provider,
            recipient=recipient
        ).exists()
        
        return not existing_feedback

    @staticmethod
    @transaction.atomic
    def create(provider: Person, recipient: Person, **kwargs) -> Feedback:
        """Create feedback with validation"""
        if not FeedbackService.can_leave_feedback(provider, recipient):
            raise ValidationError(_("You cannot leave feedback for this person"))

        feedback = Feedback(
            provider=provider,
            recipient=recipient,
            **kwargs
        )
        feedback.full_clean()
        feedback.save()
        return feedback

    @staticmethod
    @transaction.atomic
    def update(feedback_id: int, **kwargs) -> Feedback:
        """Update existing feedback"""
        feedback = Feedback.objects.get(id=feedback_id)
        for key, value in kwargs.items():
            setattr(feedback, key, value)
        feedback.full_clean()
        feedback.save()
        return feedback

    @staticmethod
    def delete(feedback_id: int, deleting_user: Person) -> None:
        """Delete feedback with authorization check"""
        try:
            feedback = Feedback.objects.get(id=feedback_id)
            if feedback.provider != deleting_user:
                raise ValidationError(_("You can only delete your own feedback"))
            feedback.delete()
        except ObjectDoesNotExist:
            raise ValidationError(_("Feedback not found"))

    @staticmethod
    def get_analytics_for_person(person: Person) -> dict:
        """
        Generates the analytics that a Talent receives through the time he/she spent
        on the platform.
        """
        feedbacks = Feedback.objects.filter(recipient=person)

        total_feedbacks = feedbacks.count()

        if total_feedbacks == 0:
            total_feedbacks = 1

        feedback_aggregates = feedbacks.aggregate(feedback_count=Count("id"), average_stars=Avg("stars"))

        # Calculate percentages
        feedback_aggregates["average_stars"] = (
            round(feedback_aggregates["average_stars"], 1) if feedback_aggregates["average_stars"] is not None else 0
        )

        stars_counts = feedbacks.values("stars").annotate(count=Count("id"))

        stars_percentages = {star: int(round(0 / total_feedbacks * 100, 2)) for star in range(1, 6)}

        for entry in stars_counts:
            stars_percentages[entry["stars"]] = round(entry["count"] / total_feedbacks * 100, 1)

        feedback_aggregates.update(stars_percentages)

        return feedback_aggregates

    @staticmethod
    def get_person_feedbacks(person: Person) -> QuerySet:
        """Get all feedbacks for a person with related data"""
        return (Feedback.objects
                .filter(recipient=person)
                .select_related('provider')
                .order_by('-created_at'))


class SkillService:
    @staticmethod
    def get_current_skills(person: Person) -> List[int]:
        """Get list of current skill IDs for person"""
        try:
            return list(PersonSkill.objects
                       .filter(person=person)
                       .values_list('skill__id', flat=True))
        except (ObjectDoesNotExist, AttributeError):
            return []

    @staticmethod
    def get_all_active_skills() -> List[dict]:
        """Get all active skills ordered by boost factor"""
        return list(Skill.objects
                   .filter(active=True)
                   .order_by("-display_boost_factor")
                   .values())
