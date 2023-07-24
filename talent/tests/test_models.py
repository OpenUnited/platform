from django.test import TestCase

from .factories import ProfileFactory


class ProfileModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.profile = ProfileFactory.build(
            first_name="Test",
            last_name="User",
        )

    def test_str_method(self):
        self.assertEqual(str(self.profile), "Test User")

    def test_default_values(self):
        self.assertTrue(self.profile.send_me_bounties)
        self.assertTrue(self.profile.is_active)
        self.assertFalse(self.profile.is_test_user)
        self.assertFalse(self.profile.is_staff)

    # TODO
    def test_photo_upload(self):
        pass
