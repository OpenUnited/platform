from django.test import TestCase
from django.contrib.auth import get_user_model

from .factories import UserFactory


class UserManagerTest(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = UserFactory(username="testuser", password="12345")

    def test_get_or_none(self):
        user = self.User.objects.get_or_none(username="testuser")
        self.assertIsNotNone(user)

        user = self.User.objects.get_or_none(username="doesnotexist")
        self.assertIsNone(user)
