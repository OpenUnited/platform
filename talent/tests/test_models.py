from django.test import TestCase

from .factories import PersonFactory


class PersonModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory.build(
            first_name="Test",
            last_name="User",
        )

    def test_str_method(self):
        self.assertEqual(str(self.person), "Test User")

    def test_default_values(self):
        self.assertTrue(self.person.send_me_bounties)
        self.assertTrue(self.person.is_active)
        self.assertFalse(self.person.is_test_user)
        self.assertFalse(self.person.is_staff)

    # TODO
    def test_photo_upload(self):
        pass
