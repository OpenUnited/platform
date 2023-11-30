from django.test import TestCase
import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice, FuzzyText

from .factories import PersonFactory
from talent.models import Status, BountyDeliveryAttempt
from product_management.tests.factories import BountyClaimFactory


# This class should be in talent/tests/factories.py but putting in
# there creates a very complex circular import error. That is why
# it is put in here.
class BountyDeliveryAttemptFactory(DjangoModelFactory):
    bounty_claim = factory.SubFactory(BountyClaimFactory)
    person = factory.SubFactory(PersonFactory)
    delivery_message = FuzzyText()
    kind = FuzzyChoice(
        [kind[0] for kind in BountyDeliveryAttempt.SUBMISSION_TYPES]
    )
    is_canceled = False

    class Meta:
        model = BountyDeliveryAttempt


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
