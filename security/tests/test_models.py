from django.test import TestCase

from .factories import UserFactory


class UserModelTest(TestCase):
    def test_reset_remaining_budget_for_failed_logins(self):
        user_one = UserFactory.create(remaining_budget_for_failed_logins=1)
        user_one.reset_remaining_budget_for_failed_logins()

        self.assertEqual(user_one.remaining_budget_for_failed_logins, 3)

        user_two = UserFactory.create()
        user_two.reset_remaining_budget_for_failed_logins

        self.assertEqual(user_two.remaining_budget_for_failed_logins, 3)

    def test_update_failed_login_budget_and_check_reset(self):
        user_one = UserFactory.create()

        user_one.update_failed_login_budget_and_check_reset()
        self.assertEqual(user_one.remaining_budget_for_failed_logins, 2)
        self.assertFalse(user_one.password_reset_required)

        user_one.update_failed_login_budget_and_check_reset()
        self.assertEqual(user_one.remaining_budget_for_failed_logins, 1)
        self.assertFalse(user_one.password_reset_required)

        user_one.update_failed_login_budget_and_check_reset()
        self.assertEqual(user_one.remaining_budget_for_failed_logins, 0)
        self.assertTrue(user_one.password_reset_required)
