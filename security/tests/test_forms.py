from django.test import TestCase
from django.forms import ValidationError

from security.forms import SignUpStepOneForm, SignUpStepThreeForm
from .factories import UserFactory


class SignUpStepOneFormTest(TestCase):
    def setUp(self):
        self.user = UserFactory(
            username="john", password="12345", email="user@example.com"
        )

    def test_valid_email(self):
        form_data = {
            "full_name": "john doe",
            "preferred_name": "john",
            "email": "does_not_exist@example.com",
        }

        form = SignUpStepOneForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_email(self):
        form_data = {
            "full_name": "john doe",
            "preferred_name": "john",
            "email": "user@example.com",
        }

        form = SignUpStepOneForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_invalid_clean(self):
        email = "john@example.com"
        _ = UserFactory(email=email)
        form_data = {
            "full_name": "john doe",
            "preferred_name": "john",
            "email": email,
        }

        form = SignUpStepOneForm(data=form_data)

        self.assertFalse(form.is_valid())
        self.assertIsNotNone(form.errors)

        cleaned_email = form.clean_email()
        self.assertIsNone(cleaned_email)

        expected_error_message = (
            "That email isn't available, please try another"
        )
        self.assertIn(expected_error_message, form.errors.get("email", []))

    def test_valid_clean(self):
        _ = UserFactory(email="john@example.com")
        email = "not_john@example.com"
        form_data = {
            "full_name": "john doe",
            "preferred_name": "john",
            "email": email,
        }

        form = SignUpStepOneForm(data=form_data)

        self.assertTrue(form.is_valid())
        cleaned_email = form.clean_email()

        self.assertEqual(email, cleaned_email)


class SignUpStepThreeFormTest(TestCase):
    def test_valid_clean_username(self):
        _ = UserFactory(username="test_user")
        form_data = {
            "username": "does_not_exit",
            "password": "vvFTtNOWcBEKILA",
            "password_confirm": "vvFTtNOWcBEKILA",
        }

        form = SignUpStepThreeForm(data=form_data)

        self.assertTrue(form.is_valid())

        cleaned_username = form.clean_username()
        self.assertEqual(cleaned_username, "does_not_exit")

    def test_invalid_clean_username(self):
        _ = UserFactory(username="test_user")
        form_data = {
            "username": "test_user",
            "password": "vvFTtNOWcBEKILA",
            "password_confirm": "vvFTtNOWcBEKILA",
        }

        form = SignUpStepThreeForm(data=form_data)

        self.assertFalse(form.is_valid())

        cleaned_username = form.clean_username()
        self.assertIsNone(cleaned_username)

        expected_error = "Username already exists"
        self.assertIn(expected_error, form.errors.get("username"), [])

    def test_valid_clean(self):
        form_data = {
            "username": "test_user",
            "password": "vvFTtNOWcBEKILA",
            "password_confirm": "vvFTtNOWcBEKILA",
        }

        form = SignUpStepThreeForm(data=form_data)

        self.assertTrue(form.is_valid())

    def test_invalid_clean(self):
        form_data = {
            "username": "test_user",
            "password": "vvFTtNOWcBEKILA",
            "password_confirm": "vvFTtNOWcBEKILA111",
        }

        form = SignUpStepThreeForm(data=form_data)

        self.assertFalse(form.is_valid())
        with self.assertRaises(ValidationError):
            form.clean()
