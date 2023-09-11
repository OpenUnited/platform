from django.test import TestCase

from talent.services import FeedbackService
from .factories import FeedbackFactory
from talent.tests.factories import PersonFactory


class FeedbackServiceTest(TestCase):
    def setUp(self):
        self.person = PersonFactory()

    def test_analytics_with_no_feedback(self):
        stars = [1, 2, 3, 5, 3, 2]
        for star in stars:
            _ = FeedbackFactory(stars=star)

        actual = FeedbackService.get_analytics_for_person(self.person)
        expected = {
            "feedback_count": 0,
            "average_stars": 0,
            1: 0,
            2: 0,
            3: 0,
            4: 0,
            5: 0,
        }

        self.assertEqual(actual, expected)

    def test_analytics_with_one_feedback(self):
        _ = FeedbackFactory(recipient=self.person, stars=5)

        actual = FeedbackService.get_analytics_for_person(self.person)
        expected = {
            "feedback_count": 1,
            "average_stars": 5,
            1: 0,
            2: 0,
            3: 0,
            4: 0,
            5: 100,
        }

        self.assertEqual(actual, expected)

    def test_analytics_with_two_feedbacks(self):
        _ = FeedbackFactory(recipient=self.person, stars=5)
        _ = FeedbackFactory(recipient=self.person, stars=3)

        actual = FeedbackService.get_analytics_for_person(self.person)
        expected = {
            "feedback_count": 2,
            "average_stars": 4,
            1: 0,
            2: 0,
            3: 50,
            4: 0,
            5: 50,
        }

        self.assertEqual(actual, expected)

    def test_analytics_with_two_feedbacks_uneven(self):
        _ = FeedbackFactory(recipient=self.person, stars=1)
        _ = FeedbackFactory(recipient=self.person, stars=2)

        actual = FeedbackService.get_analytics_for_person(self.person)
        expected = {
            "feedback_count": 2,
            "average_stars": 1.5,
            1: 50,
            2: 50,
            3: 0,
            4: 0,
            5: 0,
        }

        self.assertEqual(actual, expected)

    def test_analytics_with_three_feedbacks_uneven(self):
        _ = FeedbackFactory(recipient=self.person, stars=1)
        _ = FeedbackFactory(recipient=self.person, stars=2)
        _ = FeedbackFactory(recipient=self.person, stars=2)

        actual = FeedbackService.get_analytics_for_person(self.person)
        expected = {
            "feedback_count": 3,
            "average_stars": 1.7,
            1: 33.3,
            2: 66.7,
            3: 0,
            4: 0,
            5: 0,
        }

        self.assertEqual(actual, expected)

    def test_analytics_with_multiple_feedbacks(self):
        _ = FeedbackFactory(recipient=self.person, stars=5)
        _ = FeedbackFactory(recipient=self.person, stars=5)
        _ = FeedbackFactory(recipient=self.person, stars=4)
        _ = FeedbackFactory(recipient=self.person, stars=4)
        _ = FeedbackFactory(recipient=self.person, stars=3)
        _ = FeedbackFactory(recipient=self.person, stars=5)
        _ = FeedbackFactory(recipient=self.person, stars=4)

        actual = FeedbackService.get_analytics_for_person(self.person)
        expected = {
            "feedback_count": 7,
            "average_stars": 4.3,
            1: 0,
            2: 0,
            3: 14.3,
            4: 42.9,
            5: 42.9,
        }

        self.assertEqual(actual, expected)
