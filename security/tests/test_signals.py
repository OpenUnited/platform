from django.test import TestCase

from .factories import UserFactory


class UserSignalTest(TestCase):
    def setUp(self):
        self.user = UserFactory.create(username="testuser", password="12345")

    def test_pre_save_receiver(self):
        self.user.password = "newpassword"
        self.user.save()

        self.assertEqual(self.user.remaining_budget_for_failed_logins, 3)
        self.assertFalse(self.user.password_reset_required)
