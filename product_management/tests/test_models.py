from django.test import TestCase
from django.urls import reverse

from security.models import ProductRoleAssignment
from .factories import ChallengeFactory, OwnedProductFactory, ProductBugFactory
from product_management.models import Bug
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


class BugModelTest(TestCase):
    def setUp(self):
        self.bug = ProductBugFactory()

    def test_get_str(self):
        expected_str = f"{self.bug.person} - {self.bug.title}"
        actual_str = str(self.bug)

        self.assertEqual(actual_str, expected_str)

    def test_get_absolute_url(self):
        expected_url = reverse(
            "add_product_bug", args=(self.bug.product.slug,)
        )
        actual_url = self.bug.get_absolute_url()

        self.assertEqual(actual_url, expected_url)
