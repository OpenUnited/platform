import logging
from django.contrib.auth import get_user_model
from django.db import transaction


from talent.models import Person, Skill, Expertise, BountyClaim, BountyDeliveryAttempt
from product_management.models import Bounty


logger = logging.getLogger(__name__)


Person = get_user_model()


class PersonService:
    @staticmethod
    def create(**kwargs):
        password = kwargs.pop("password", None)
        person = Person(**kwargs)
        if password:
            person.set_password(password)
        person.save()
        return person

    @staticmethod
    def get_by_id(id):
        person = Person.objects.get(id=id)
        return person

    @staticmethod
    def get_by_username(username: str) -> Person:
        return Person.objects.get(username=username)

    @staticmethod
    def update(person: Person, **kwargs):
        for key, value in kwargs.items():
            setattr(person, key, value)

        person.save()
        return person

    @staticmethod
    def delete(id):
        Person.objects.get(id=id).delete()

    @staticmethod
    def toggle_bounties(id):
        person = Person.objects.get(id=id)
        person.send_me_bounties = not person.send_me_bounties
        person.save()
        return person

    @staticmethod
    def make_test_user(id):
        person = Person.objects.get(id=id)
        person.is_test_user = True
        person.save()
        return person


class SkillService:
    @staticmethod
    def create(**kwargs):
        skill = Skill(**kwargs)
        skill.save()

        return skill


class ExpertiseService:
    @staticmethod
    def create(**kwargs):
        expertise = Expertise(**kwargs)
        expertise.save()

        return expertise


# TODO: This service will be deleted once ProfileService is done
# class PersonService:
#     @transaction.atomic
#     def create(
#         self,
#         user: User,
#         full_name: str,
#         preferred_name: str,
#         headline: str,
#         photo_file: str = None,
#         test_user: bool = False,
#         overview: str = "",
#         send_me_bounties: bool = True,
#     ):
#         person = Person(
#             user=user,
#             full_name=full_name,
#             preferred_name=preferred_name,
#             photo=photo_file,
#             headline=headline,
#             test_user=test_user,
#             overview=overview,
#             send_me_bounties=send_me_bounties,
#         )
#         person.save()

#         return person

#     @transaction.atomic
#     def update(
#         self,
#         email,
#         full_name=None,
#         preferred_name=None,
#         photo_file=None,
#         headline=None,
#         test_user=None,
#         overview=None,
#         send_me_bounties=None,
#     ):
#         try:
#             person = Person.objects.get(user__email=email)

#             if full_name:
#                 person.full_name = full_name
#             if preferred_name:
#                 person.preferred_name = preferred_name
#             if photo_file:
#                 person.photo = photo_file
#             if headline:
#                 person.headline = headline
#             if test_user:
#                 person.test_user = test_user
#             if overview:
#                 person.overview = overview
#             if send_me_bounties:
#                 person.send_me_bounties = send_me_bounties

#             person.save()
#         except Person.DoesNotExist as e:
#             logger.error(f"Failed to delete Person due to: {e}")
#             return None

#     @staticmethod
#     def logged_in_user(request):
#         authorized_user = request.user
#         return authorized_user

#     @staticmethod
#     def get_current_person(request):
#         user = request.user

#         if user.is_anonymous:
#             return None

#         try:
#             return Person.objects.get(user=user)
#         except Person.DoesNotExist:
#             return None

#     @staticmethod
#     def get_person(person_id):
#         if person_id is not None:
#             return Person.objects.get(pk=person_id)

#         return None

#     @staticmethod
#     def get_person_from_slug(person_slug):
#         person = Person.objects.get(user__username=person_slug)

#         return person

#     @staticmethod
#     def get_person_challenges(person_slug):
#         bounty_claims = (
#             BountyClaim.objects.filter(
#                 person__user__username=person_slug, kind=BountyClaim.CLAIM_TYPE_DONE
#             )
#             .order_by("-bounty__updated_at")
#             .select_related("bounty")
#             .all()
#         )
#         challenges = [b_claim.bounty.challenge for b_claim in bounty_claims]

#         return challenges

#     @staticmethod
#     def get_person_bounty_delivery_message(challenge_id, person_slug):
#         challenge_bounty = Bounty.objects.filter(challenge_id=challenge_id)
#         bounty_claim = None

#         for bounty in challenge_bounty:
#             bounty_claim = BountyClaim.objects.filter(
#                 bounty=bounty,
#                 kind=BountyClaim.CLAIM_TYPE_DONE,
#                 person__slug=person_slug,
#             ).last()
#             if bounty_claim:
#                 delivery_attempt = bounty_claim.delivery_attempt.filter(
#                     kind=BountyDeliveryAttempt.SUBMISSION_TYPE_APPROVED
#                 ).last()
#                 if delivery_attempt:
#                     return delivery_attempt

#         return None
