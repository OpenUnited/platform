from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
import factory

from talent.models import (
    Skill,
    Expertise,
    PersonSkill,
    Feedback,
    BountyDeliveryAttempt,
)
from .factories import (
    SkillFactory,
    ExpertiseFactory,
    PersonFactory,
    PersonSkillFactory,
    FeedbackFactory,
)
from product_management.tests.factories import (
    BountyClaimFactory,
    ChallengeFactory,
    BountyFactory,
)


class TalentAppLoginRequiredTest(TestCase):
    def setUp(self):
        self.url_names = [
            "get_skills",
            "get_current_skills",
            "get_expertise",
            "get_current_expertise",
            "list-skill-and-expertise",
        ]
        self.url_list = [reverse(url_name) for url_name in self.url_names]

    def test_as_anonymous(self):
        login_url = reverse("sign_in")
        client = Client()

        for url in self.url_list:
            response = client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, f"{login_url}?next={url}")

    def test_as_logged_in(self):
        person = PersonFactory()
        client = Client()
        client.force_login(person.user)

        for url in self.url_list:
            response = client.get(url)
            self.assertEqual(response.status_code, 200)


class TalentAppFunctionBasedViewsTest(TestCase):
    def setUp(self):
        self.person = PersonFactory()
        self.client = Client()
        self.client.force_login(self.person.user)

        self.another_person = PersonFactory()
        self.client_for_none = Client()
        self.client_for_none.force_login(self.another_person.user)
        self.skill = SkillFactory.create()
        self.expertise = ExpertiseFactory.create_batch(10, skill=self.skill)

        _ = PersonSkillFactory(
            person=self.person,
            skill=self.skill,
            expertise=self.expertise,
        )


class TalentPortfolioViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        person_auth = PersonFactory()
        self.client.force_login(person_auth.user)

        self.person = PersonFactory()
        self.person_skill = PersonSkillFactory(person=self.person)
        self.url = reverse("portfolio", args=(self.person.user.username,))

    def test_get_request(self):
        from talent.services import FeedbackService

        client = Client()
        response = client.get(self.url)

        actual = response.context_data

        # we dont' need to check form
        actual.pop("form")

        expected = {
            "user": self.person.user,
            "person": self.person,
            "person_linkedin_link": "",
            "person_twitter_link": "",
            "status": self.person.status,
            "expertise": self.person_skill.expertise,
            "FeedbackService": FeedbackService,
            "can_leave_feedback": False,
        }

        bounty_claims = actual.pop("bounty_claims")
        self.assertEqual(bounty_claims.count(), 0)

        received_feedbacks = actual.pop("received_feedbacks")
        self.assertEqual(received_feedbacks.count(), 0)

        # self.assertEqual(actual, expected)

        response = self.client.get(self.url)

        # actual = response.context_data
        expected = {
            "user": self.person.user,
            "person": self.person,
            "person_linkedin_link": "",
            "person_twitter_link": "",
            "status": self.person.status,
            "expertise": self.person_skill.expertise,
            "FeedbackService": FeedbackService,
            "can_leave_feedback": True,
        }

        self.assertEqual(bounty_claims.count(), 0)
        self.assertEqual(received_feedbacks.count(), 0)

        # self.assertEqual(actual, expected)


# TODO: write tests for _remove_picture method. It is not written since it was not urgent
class UpdateProfileViewTest(TestCase):
    def setUp(self):
        self.person = PersonFactory()
        self.client = Client()
        self.client.force_login(self.person.user)
        self.url = reverse("profile", args=(self.person.user.pk,))

    def test_post_valid(self):
        skills = SkillFactory.create_batch(3)
        expertise = ExpertiseFactory.create_batch(5)
        data = {
            "full_name": "test user",
            "preferred_name": "test",
            "current_position": "xyz company",
            "headline": "dummy headline",
            "overview": "dummy overview",
            "location": "somewhere",
            "github_link": "www.github.com/testuser",
            "twitter_link": "www.twitter.com/testuser",
            "linkedin_link": "www.linkedin.com/in/testuser",
            "website_link": "www.example.com",
            "send_me_bounties": True,
        }

        _ = self.client.post(self.url, data=data)


class CreateFeedbackViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("create-feedback")
        self.login_url = reverse("sign_in")
        self.recipient = PersonFactory()
        self.provider = PersonFactory()

    def test_post(self):
        # Test login required
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"{self.login_url}?next={self.url}")

        # Test Feedback object creation
        self.client.force_login(self.provider.user)
        data = {
            "recipient": self.recipient,
            "provider": self.provider,
            "message": "Test test test",
            "stars": 5,
        }

        response = self.client.post(
            self.url,
            data=data,
            headers={
                "Referer": f"http://example.com/talent/portfolio/{self.recipient.user.username}"
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("portfolio", args=(self.recipient.user.username,)),
        )
        self.assertGreater(
            Feedback.objects.filter(provider=self.provider).count(), 0
        )


class UpdateFeedbackViewTest(TestCase):
    def setUp(self):
        self.feedback = FeedbackFactory()
        self.url = reverse("update-feedback", args=(self.feedback.id,))
        self.person = PersonFactory()
        self.client = Client()
        self.login_url = reverse("sign_in")

    def test_post(self):
        # Test login required
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"{self.login_url}?next={self.url}")

        # Test Feedback object update
        self.client.force_login(self.person.user)
        data = {
            "message": "Update message",
            "stars": 4,
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse(
                "portfolio", args=(self.feedback.recipient.user.username,)
            ),
        )

        obj = Feedback.objects.get(pk=self.feedback.pk)
        self.assertEqual(obj.message, data.get("message"))
        self.assertEqual(obj.stars, data.get("stars"))


class DeleteFeedbackViewTest(TestCase):
    def setUp(self):
        self.feedback = FeedbackFactory()
        self.url = reverse("delete-feedback", args=(self.feedback.id,))
        self.person = PersonFactory()
        self.client = Client()
        self.login_url = reverse("sign_in")

    def test_post(self):
        # Test login required
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

        login_url = reverse("sign_in")
        self.assertEqual(response.url, f"{login_url}?next={self.url}")

        # Test Feedback object delete
        self.client.force_login(self.person.user)
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse(
                "portfolio", args=(self.feedback.recipient.user.username,)
            ),
        )

        with self.assertRaises(ObjectDoesNotExist):
            Feedback.objects.get(pk=self.feedback.pk)


class CreateBountyDeliveryAttempViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        challenge = ChallengeFactory()
        bounty = BountyFactory(challenge=challenge)
        self.url = reverse(
            "create-bounty-delivery-attempt",
            args=(challenge.product.slug, challenge.id, bounty.id),
        )
        self.person = PersonFactory()
        self.login_url = reverse("sign_in")

    def test_anon(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{self.login_url}?next={self.url}")

    def test_valid_post(self):
        self.client.force_login(self.person.user)

        bounty_claim = BountyClaimFactory(person=self.person)
        data = {
            "bounty_claim": bounty_claim.id,
            "kind": 0,  # SUBMISSION_TYPE_NEW
            "person": self.person.id,
            "delivery_message": "test test test",
        }
        response = self.client.post(f"{self.url}?id={bounty_claim.id}", data)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("dashboard"))

        work_submission = BountyDeliveryAttempt.objects.last()

        self.assertEqual(work_submission.kind, data.get("kind"))
        self.assertEqual(
            work_submission.delivery_message, data.get("delivery_message")
        )
        self.assertEqual(work_submission.person.id, data.get("person"))
