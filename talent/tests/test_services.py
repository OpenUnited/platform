from django.contrib.auth.hashers import check_password
from django.test import TestCase

from talent.tests.factories import PersonFactory
from talent.models import Person
from talent.services import PersonService


class PersonServiceTest(TestCase):
    def setUp(self):
        self.person = PersonFactory.create(username="username")
        self.to_toggle = PersonFactory.create(send_me_bounties=True)
        self.to_make_test_user = PersonFactory.create(is_test_user=False)

    def test_create(self):
        person = PersonService.create(
            first_name="Test",
            last_name="User",
            email="test+gary@openunited.com",
            username="garyg",
            password="123456789",
            headline="Lorem ipsum sit amet",
            overview="Test test test",
        )

        self.assertIsInstance(person, Person)
        self.assertEqual(person.first_name, "Test")
        self.assertEqual(person.last_name, "User")
        self.assertEqual(person.email, "test+gary@openunited.com")
        self.assertEqual(person.username, "garyg")
        self.assertTrue(check_password("123456789", person.password))
        self.assertEqual(person.headline, "Lorem ipsum sit amet")
        self.assertEqual(person.overview, "Test test test")

    def test_update(self):
        updated_person = PersonService.update(self.person, username="updated_username")

        self.assertEqual(updated_person.username, "updated_username")

    def test_toggle_bounties(self):
        self.assertTrue(self.to_toggle.send_me_bounties)
        self.to_toggle = PersonService.toggle_bounties(self.to_toggle.id)
        self.assertFalse(self.to_toggle.send_me_bounties)
        self.to_toggle = PersonService.toggle_bounties(self.to_toggle.id)
        self.assertTrue(self.to_toggle.send_me_bounties)

    def test_make_test_user(self):
        self.assertFalse(self.to_make_test_user.is_test_user)
        self.to_make_test_user = PersonService.make_test_user(self.to_make_test_user.id)
        self.assertTrue(self.to_make_test_user.is_test_user)
