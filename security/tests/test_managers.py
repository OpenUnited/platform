from django.test import TestCase
from django.contrib.auth import get_user_model

from .factories import UserFactory


class UserManagerTest(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = UserFactory(
            username="testuser", email="testuser@example.com", password="12345"
        )

    def test_get_or_none(self):
        user = self.User.objects.get_or_none(username="testuser")
        self.assertIsNotNone(user)

        user = self.User.objects.get_or_none(username="doesnotexist")
        self.assertIsNone(user)

    def test_get_user_by_username_or_email(self):
        # Case 1: None
        actual = self.User.objects.get_user_by_username_or_email(
            username="does_not_exist"
        )
        self.assertIsNone(actual)

        actual = self.User.objects.get_user_by_username_or_email(
            username="does_not_exist"
        )
        self.assertIsNone(actual)

        # Case 2: Single object returned
        actual = self.User.objects.get_user_by_username_or_email(
            username=self.user.username
        )
        self.assertEqual(self.user, actual)

        actual = self.User.objects.get_user_by_username_or_email(
            username=self.user.email
        )
        self.assertEqual(self.user, actual)
