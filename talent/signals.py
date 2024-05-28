from django.db.models.signals import post_save
from django.dispatch import receiver

from product_management.models import Bounty, Challenge

from .models import BountyClaim, BountyDeliveryAttempt, Person, Status


@receiver(post_save, sender=Person)
def create_status_for_person(sender, instance, created, **kwargs):
    if created:
        _ = Status.objects.create(person=instance)


@receiver(post_save, sender=BountyDeliveryAttempt)
def update_bounty_delivery_status(sender, instance, created, **kwargs):
    if not created:
        action_mapping = {
            BountyDeliveryAttempt.SubmissionType.APPROVED: {
                "bounty_claim_status": BountyClaim.Status.COMPLETED,
                "bounty_status": Bounty.BountyStatus.COMPLETED,
                "challenge_status": Challenge.ChallengeStatus.choices,
            },
            BountyDeliveryAttempt.SubmissionType.REJECTED: {
                "bounty_claim_status": BountyClaim.Status.FAILED,
                "bounty_status": Bounty.BountyStatus.AVAILABLE,
                "challenge_status": Challenge.ChallengeStatus.ACTIVE,
            },
        }

        actions = action_mapping.get(instance.kind, {})

        if actions:
            instance.bounty_claim.status = actions["bounty_claim_status"]
            instance.bounty_claim.save()

            instance.bounty_claim.bounty.status = actions["bounty_status"]
            instance.bounty_claim.bounty.save()

            instance.bounty_claim.bounty.challenge.status = actions["challenge_status"]
            instance.bounty_claim.bounty.challenge.save()
