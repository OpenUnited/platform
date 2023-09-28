from django.test import TestCase

from security.models import ProductRoleAssignment
from .factories import ChallengeFactory, OwnedProductFactory
from security.tests.factories import ProductRoleAssignmentFactory
from talent.tests.factories import PersonFactory


class ChallengeModelTest(TestCase):
    def setUp(self):
        self.person = PersonFactory()
        self.product = OwnedProductFactory()
        self.challenge = ChallengeFactory(product=self.product)
        self.challenge_no_product = ChallengeFactory(product=None)

    def test_can_delete_challenge(self):
        response = self.challenge_no_product.can_delete_challenge(self.person)
        self.assertFalse(response)

        response = self.challenge.can_delete_challenge(self.person)
        self.assertFalse(response)

        product_role_assignment = ProductRoleAssignmentFactory(
            person=self.person,
            product=self.product,
            role=ProductRoleAssignment.CONTRIBUTOR,
        )

        response = self.challenge.can_delete_challenge(self.person)
        self.assertFalse(response)

        product_role_assignment.role = ProductRoleAssignment.PRODUCT_ADMIN
        product_role_assignment.save()

        response = self.challenge.can_delete_challenge(self.person)
        self.assertTrue(response)
