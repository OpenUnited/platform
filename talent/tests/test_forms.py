from django import forms
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from talent.forms import SignInForm, SignUpForm, PersonDetailsForm
from .factories import PersonFactory


class SignInFormTest(TestCase):
    def test_form_fields(self):
        form = SignInForm()

        self.assertIn("username", form.fields)
        self.assertIsInstance(form.fields["username"], forms.CharField)
        self.assertEqual(form.fields["username"].max_length, 150)

        self.assertIn("password", form.fields)
        self.assertIsInstance(form.fields["password"], forms.CharField)
        self.assertEqual(form.fields["password"].max_length, 128)

    def test_form_validation(self):
        form = SignInForm(
            {
                "username": "testusername",
                "password": "testpassword",
            }
        )
        self.assertTrue(form.is_valid())

        form = SignInForm(
            {
                "password": "testpassword",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

        form = SignInForm(
            {
                "username": "testusername",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("password", form.errors)


class SignUpFormTest(TestCase):
    def test_form_fields(self):
        form = SignUpForm()

        self.assertIn("first_name", form.fields)
        self.assertIn("last_name", form.fields)
        self.assertIn("username", form.fields)
        self.assertIn("email", form.fields)
        self.assertIn("password1", form.fields)
        self.assertIn("password2", form.fields)

    def test_form_validation(self):
        form = SignUpForm(
            {
                "first_name": "Test",
                "last_name": "User",
                "username": "testusername",
                "email": "test@example.com",
                "password1": "testpassword",
                "password2": "testpassword",
            }
        )
        self.assertTrue(form.is_valid())

        form = SignUpForm(
            {
                "last_name": "User",
                "username": "testusername",
                "password1": "testpassword",
                "password2": "testpassword",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("first_name", form.errors)
        self.assertIn("email", form.errors)

    def test_user_creation(self):
        form = SignUpForm(
            {
                "first_name": "Test",
                "last_name": "User",
                "username": "testusername",
                "email": "test@example.com",
                "password1": "testpassword",
                "password2": "testpassword",
            }
        )
        self.assertTrue(form.is_valid())

        user = form.save()
        self.assertEqual(user.first_name, "Test")
        self.assertEqual(user.last_name, "User")
        self.assertEqual(user.username, "testusername")
        self.assertEqual(user.email, "test@example.com")

        self.assertTrue(user.check_password("testpassword"))


# TODO: test photo uploading
class PersonDetailsFormTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = PersonFactory()

    def test_form_fields(self):
        form = PersonDetailsForm(instance=self.user)

        self.assertIn("headline", form.fields)
        self.assertIn("overview", form.fields)
        self.assertIn("photo", form.fields)

    def test_form_validation(self):
        form = PersonDetailsForm(
            {
                "headline": "A great headline",
                "overview": "An interesting overview",
                "photo": SimpleUploadedFile(
                    "file.jpg", b"file_content", content_type="image/jpg"
                ),
            },
            instance=self.user,
        )
        self.assertTrue(form.is_valid())

        form = PersonDetailsForm(
            {
                "overview": "An interesting overview",
                "photo": SimpleUploadedFile(
                    "file.jpg", b"file_content", content_type="image/jpg"
                ),
            },
            instance=self.user,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("headline", form.errors)

    def test_person_update(self):
        form = PersonDetailsForm(
            {
                "headline": "A great headline",
                "overview": "An interesting overview",
                # "photo": SimpleUploadedFile(
                #     "file.jpg", b"file_content", content_type="image/jpg"
                # ),
            },
            instance=self.user,
        )

        self.assertTrue(form.is_valid())

        person = form.save()
        self.assertEqual(person.headline, "A great headline")
        self.assertEqual(person.overview, "An interesting overview")
        # self.assertEqual(person.photo.name, "file.jpg")
