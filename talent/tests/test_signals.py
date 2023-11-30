from django.test import TestCase

from talent.models import Status, BountyDeliveryAttempt
from .factories import BountyDeliveryAttemptFactory


class PersonRelatedTest(TestCase):
    def test_create_status_for_person(self):
        from .factories import PersonFactory

        person = PersonFactory()
        status = person.status

        self.assertEqual(status.name, Status.DRONE)
        self.assertEqual(status.points, 0)


class BountyDeliveryAttemptRelatedTest(TestCase):
    def setUp(self):
        self.bounty_delivery = BountyDeliveryAttemptFactory(
            kind=BountyDeliveryAttempt.SUBMISSION_TYPE_NEW,
        )

    def test_approved(self):
        self.bounty_delivery.kind = (
            BountyDeliveryAttempt.SUBMISSION_TYPE_APPROVED
        )
        self.bounty_delivery.save()

        self.assertEqual(self.bounty_delivery.kind, 1)
        self.assertEqual(self.bounty_delivery.bounty_claim.kind, 0)
        self.assertEqual(self.bounty_delivery.bounty_claim.bounty.status, 4)
        self.assertEqual(
            self.bounty_delivery.bounty_claim.bounty.challenge.status, 4
        )


def test_rejected(self):
    self.bounty_delivery.kind = BountyDeliveryAttempt.SUBMISSION_TYPE_REJECTED
    self.bounty_delivery.save()

    self.assertEqual(self.bounty_delivery.kind, 2)
    self.assertEqual(self.bounty_delivery.bounty_claim.kind, 2)
    self.assertEqual(self.bounty_delivery.bounty_claim.bounty.status, 2)
    self.assertEqual(
        self.bounty_delivery.bounty_claim.bounty.challenge.status, 2
    )
