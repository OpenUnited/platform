from typing import Dict, List, Optional, Tuple
from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied, ObjectDoesNotExist
from django.db.models import QuerySet, Avg, Count
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
import json

from apps.capabilities.product_management.models import Bounty
from apps.capabilities.talent.forms import PersonProfileForm, PersonSkillFormSet
from apps.common.exceptions import ServiceException, InvalidInputError, AuthorizationError, ResourceNotFoundError
from . import utils

from .models import (
    Person, PersonSkill, Skill, Expertise, 
    Feedback, BountyClaim, BountyDeliveryAttempt
)
from apps.capabilities.security.models import ProductRoleAssignment
from django.core.cache import cache


class ProfileService:
    @staticmethod
    def get_user_profile(username: str) -> Person:
        """Get user profile with related data"""
        try:
            return Person.objects.select_related('user').get(
                user__username=username
            )
        except ObjectDoesNotExist:
            raise ResourceNotFoundError(f"User {username} not found")

    @staticmethod
    @transaction.atomic
    def update_profile(person: Person, profile_data: dict, skills_data: list) -> Person:
        """Update profile and associated skills"""
        try:
            # Validate inputs
            if not isinstance(profile_data, dict):
                raise InvalidInputError("Profile data must be a dictionary")
            if not isinstance(skills_data, list):
                raise InvalidInputError("Skills data must be a list")

            with transaction.atomic():
                # Update basic profile fields
                for key, value in profile_data.items():
                    if not hasattr(person, key):
                        raise InvalidInputError(f"Invalid profile field: {key}")
                    setattr(person, key, value)
                person.full_clean()
                person.save()

                # Update skills
                PersonSkill.objects.filter(person=person).delete()
                for skill_data in skills_data:
                    if not skill_data.get('skill'):
                        continue
                    
                    # Validate skill exists
                    if not Skill.objects.filter(id=skill_data['skill']).exists():
                        raise InvalidInputError(f"Invalid skill ID: {skill_data['skill']}")
                    
                    expertise_ids = skill_data.get('expertise', [])
                    if expertise_ids:
                        # Validate expertise belongs to skill
                        valid_expertise = Expertise.objects.filter(
                            id__in=expertise_ids,
                            skill_id=skill_data['skill']
                        ).count() == len(expertise_ids)
                        
                        if not valid_expertise:
                            raise InvalidInputError("Invalid expertise for skill")
                    
                    PersonSkill.objects.create(
                        person=person,
                        skill_id=skill_data['skill'],
                        expertise_ids=expertise_ids
                    )
                
                return person
                
        except ValidationError as e:
            raise InvalidInputError(str(e))
        except Exception as e:
            raise ServiceException(f"Error updating profile: {str(e)}", details=str(e))

    @staticmethod
    def get_active_skills() -> QuerySet:
        """Get all active skills ordered by boost factor"""
        return (Skill.objects
                .filter(active=True)
                .order_by('-display_boost_factor'))

    @staticmethod
    def get_expertises_for_skill(skill_id: Optional[int]) -> QuerySet:
        """Get expertise hierarchy for a skill"""
        queryset = (Expertise.get_roots()
            .prefetch_related('expertise_children')
            .select_related('skill'))
        if skill_id:
            queryset = queryset.filter(skill_id=skill_id)
        return queryset

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

    @staticmethod
    def get_expertise_context(skill_id: Optional[int], index: int) -> dict:
        """Get context data for expertise view"""
        context = {'index': index}
        
        if skill_id:
            context['expertises'] = ProfileService.get_expertises_for_skill(skill_id)
        
        return context


class ShowcaseService:
    @staticmethod
    def get_showcase_data(username: str, viewing_user=None) -> Dict:
        try:
            person = Person.objects.select_related(
                'user'
            ).prefetch_related(
                'feedback_received',
                'feedback_received__provider'
            ).get(user__username=username)

            return {
                'person': person,
                'user': person.user,
                'person_skills': person.skills.all(),
                'bounty_claims': person.bounty_claims.all(),
                'received_feedbacks': person.feedback_received.all(),
                'can_leave_feedback': (
                    viewing_user and 
                    not viewing_user.is_anonymous and 
                    FeedbackService.can_leave_feedback(
                        provider=viewing_user.person,
                        recipient=person
                    )
                )
            }
        except ObjectDoesNotExist:
            raise ResourceNotFoundError(f"User {username} not found")
        except Exception as e:
            raise ServiceException(f"Error getting showcase data: {str(e)}")

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
        try:
            required_fields = ['description']
            if not all(field in attempt_data for field in required_fields):
                raise InvalidInputError("Missing required fields in attempt data")

            with transaction.atomic():
                attempt = BountyDeliveryAttempt.objects.create(
                    person=person,
                    bounty_claim=bounty_claim,
                    kind=BountyDeliveryAttempt.SubmissionType.NEW,
                    **attempt_data
                )

                bounty_claim.status = BountyClaim.Status.CONTRIBUTED
                bounty_claim.save()

                return attempt
        except ValidationError as e:
            raise InvalidInputError(str(e))
        except Exception as e:
            raise ServiceException(f"Error creating delivery attempt: {str(e)}", details=str(e))

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
                raise AuthorizationError(_("You can only delete your own feedback"))
            feedback.delete()
        except ObjectDoesNotExist:
            raise ResourceNotFoundError(_("Feedback not found"))

    @staticmethod
    def get_analytics_for_person(person: Person) -> dict:
        """Get feedback analytics for person"""
        feedbacks = Feedback.objects.filter(recipient=person)
        
        # Get all aggregates in one query
        aggregates = feedbacks.aggregate(
            feedback_count=Count("id"),
            average_stars=Avg("stars"),
            **{f"stars_{i}_count": Count("id", filter=models.Q(stars=i))
               for i in range(1, 6)}
        )

    @staticmethod
    def get_person_feedbacks(person: Person) -> QuerySet:
        """Get all feedbacks for a person with related data"""
        return (Feedback.objects
                .filter(recipient=person)
                .select_related('provider')
                .order_by('-created_at'))

    @staticmethod
    def get_feedback(feedback_id: int) -> Feedback:
        """Get feedback by ID"""
        return get_object_or_404(Feedback, id=feedback_id)


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
        """Get all active skills with caching"""
        cache_key = 'active_skills'
        cached_skills = cache.get(cache_key)
        
        if cached_skills is None:
            skills = list(Skill.objects
                .filter(active=True)
                .order_by("-display_boost_factor")
                .values())
            cache.set(cache_key, skills, timeout=3600)  # Cache for 1 hour
            return skills
            
        return cached_skills

    @staticmethod
    def get_person_expertise(person: Person) -> Dict[str, List]:
        """
        Get all expertise for a person's skills
        
        Args:
            person: The Person object to get expertise for
            
        Returns:
            Dict containing:
            - expertiseList: List of expertise objects
            - expertiseIDList: List of expertise IDs
        """
        expertise_ids = (PersonSkill.objects
            .filter(person=person)
            .values_list('expertise', flat=True))
        
        expertise = (Expertise.objects
            .filter(id__in=expertise_ids)
            .values())
        
        return {
            "expertiseList": list(expertise),
            "expertiseIDList": list(expertise_ids)
        }

    @staticmethod
    def get_skill_expertise_pairs(expertise_ids: str = None, skills: str = None) -> List[Dict[str, str]]:
        """
        Get skill and expertise pairs for given expertise IDs
        
        Args:
            expertise_ids: JSON string of expertise IDs
            skills: Skills filter parameter (optional)
            
        Returns:
            List of dicts containing skill/expertise name pairs
            
        Raises:
            ValidationError: If expertise_ids is invalid JSON or IDs don't exist
        """
        if not expertise_ids or not skills:
            return []
            
        try:
            expertise_id_list = json.loads(expertise_ids)
        except json.JSONDecodeError:
            raise ValidationError("Invalid expertise IDs format")
            
        expertise_pairs = (Expertise.objects
            .filter(id__in=expertise_id_list)
            .select_related('skill')
            .values('skill__name', 'name'))
            
        return [
            {
                "skill": pair['skill__name'],
                "expertise": pair['name']
            }
            for pair in expertise_pairs
        ]


class PersonStatusService:
    @staticmethod
    def get_status_and_points(person: Person) -> dict:
        """Get person's status and points information"""
        return {
            'status': person.get_points_status(),
            'points': person.points,
            'next_status': person.get_next_status(),
            'points_needed': person.get_points_needed_for_next_status()
        }
