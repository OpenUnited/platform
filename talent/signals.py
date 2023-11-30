from django.db.models.signals import post_save
from django.dispatch import receiver

from product_management.models import Bounty, Challenge
from .models import Person, Status, BountyClaim, BountyDeliveryAttempt


@receiver(post_save, sender=Person)
def create_status_for_person(sender, instance, created, **kwargs):
    if created:
        _ = Status.objects.create(person=instance)


@receiver(post_save, sender=BountyDeliveryAttempt)
def update_bounty_delivery_status(sender, instance, created, **kwargs):
    if not created:
        action_mapping = {
            BountyDeliveryAttempt.SUBMISSION_TYPE_APPROVED: {
                "bounty_claim_kind": BountyClaim.CLAIM_TYPE_DONE,
                "bounty_status": Bounty.BOUNTY_STATUS_DONE,
                "challenge_status": Challenge.CHALLENGE_STATUS_DONE,
            },
            BountyDeliveryAttempt.SUBMISSION_TYPE_REJECTED: {
                "bounty_claim_kind": BountyClaim.CLAIM_TYPE_FAILED,
                "bounty_status": Bounty.BOUNTY_STATUS_AVAILABLE,
                "challenge_status": Challenge.CHALLENGE_STATUS_AVAILABLE,
            },
        }

        actions = action_mapping.get(instance.kind, {})

        if actions:
            instance.bounty_claim.kind = actions["bounty_claim_kind"]
            instance.bounty_claim.save()

            instance.bounty_claim.bounty.kind = actions["bounty_status"]
            instance.bounty_claim.bounty.save()

            instance.bounty_claim.bounty.challenge.status = actions[
                "challenge_status"
            ]
            instance.bounty_claim.bounty.challenge.save()
