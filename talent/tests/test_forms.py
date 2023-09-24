from django.test import TestCase
from django.forms import ValidationError

from talent.forms import FeedbackForm


class FeedbackFormTest(TestCase):
    def setUp(self):
        pass

    def test_valid(self):
        form_data = {
            "message": "aaaaaa",
            "stars": "5",
        }

        form = FeedbackForm(form_data)
        self.assertTrue(form.is_valid())

    def test_valid_with_parsing(self):
        form_data = {
            "message": "aaaaaa",
            "stars": "star-5",
        }

        form = FeedbackForm(form_data)
        self.assertTrue(form.is_valid())

    def test_invalid(self):
        form_data = {
            "message": "aaaaaa",
            "stars": "aaa",
        }

        form = FeedbackForm(form_data)
        self.assertFalse(form.is_valid())

        with self.assertRaises(ValidationError):
            form.clean()
