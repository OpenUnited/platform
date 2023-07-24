from django.contrib.auth.hashers import check_password
from django.test import TestCase

from talent.tests.factories import ProfileFactory
from talent.models import Profile
from talent.services import ProfileService


class ProfileServiceTest(TestCase):
    def setUp(self):
        self.profile = ProfileFactory.create(username="username")
        self.to_toggle = ProfileFactory.create(send_me_bounties=True)
        self.to_make_test_user = ProfileFactory.create(is_test_user=False)

    def test_create(self):
        profile = ProfileService.create(
            first_name="Test",
            last_name="User",
            email="test+gary@openunited.com",
            username="garyg",
            password="123456789",
            headline="Lorem ipsum sit amet",
            overview="Test test test",
        )

        self.assertIsInstance(profile, Profile)
        self.assertEqual(profile.first_name, "Test")
        self.assertEqual(profile.last_name, "User")
        self.assertEqual(profile.email, "test+gary@openunited.com")
        self.assertEqual(profile.username, "garyg")
        self.assertTrue(check_password("123456789", profile.password))
        self.assertEqual(profile.headline, "Lorem ipsum sit amet")
        self.assertEqual(profile.overview, "Test test test")

    def test_update(self):
        updated_profile = ProfileService.update(
            self.profile, username="updated_username"
        )

        self.assertEqual(updated_profile.username, "updated_username")

    def test_toggle_bounties(self):
        self.assertTrue(self.to_toggle.send_me_bounties)
        self.to_toggle = ProfileService.toggle_bounties(self.to_toggle.id)
        self.assertFalse(self.to_toggle.send_me_bounties)
        self.to_toggle = ProfileService.toggle_bounties(self.to_toggle.id)
        self.assertTrue(self.to_toggle.send_me_bounties)

    def test_make_test_user(self):
        self.assertFalse(self.to_make_test_user.is_test_user)
        self.to_make_test_user = ProfileService.make_test_user(
            self.to_make_test_user.id
        )
        self.assertTrue(self.to_make_test_user.is_test_user)
