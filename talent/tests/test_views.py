from django.test import TestCase, Client
from django.urls import reverse

from talent.models import Skill, Expertise, BountyClaim, Feedback, PersonSkill
from .factories import (
    SkillFactory,
    ExpertiseFactory,
    PersonFactory,
    StatusFactory,
    PersonSkillFactory,
)


class TalentFunctionBasedViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.skills_url = reverse("get_skills")
        self.expertise_url = reverse("get_expertise")
        self.list_skill_and_expertise_url = reverse("list-skill-and-expertise")

    def _create_skills(self, n):
        skill_ids = []
        skills = []
        for i in range(n, 0, -1):
            s = SkillFactory(display_boost_factor=i)
            skills.append(s)
            skill_ids.append(s.id)

        return skills, skill_ids

    def _create_expertise(self, skills):
        expertise_ids = []
        expertise_list = []
        for skill in skills:
            exp = ExpertiseFactory(skill=skill)
            expertise_list.append(exp)
            expertise_ids.append(exp.id)

        return expertise_list, expertise_ids

    def test_get_skills(self):
        _, skill_ids = self._create_skills(10)

        actual_response = self.client.get(self.skills_url)
        actual_json_data = actual_response.json()

        expected_json_data = list(
            Skill.objects.filter(id__in=skill_ids, active=True).values()
        )

        self.assertEqual(actual_json_data, expected_json_data)

    def test_get_skills_none(self):
        actual_response = self.client.get(self.skills_url)
        actual_json_data = actual_response.json()
        expected_json_data = []

        self.assertEqual(actual_json_data, expected_json_data)

    def test_get_expertise(self):
        skills, skill_ids = self._create_skills(5)

        _, _ = self._create_expertise(skills)

        response = self.client.get(
            self.expertise_url, data={"selected_skills": f"{skill_ids}"}
        )
        actual_data = response.json()
        expected_data = list(Expertise.objects.filter(skill_id__in=skill_ids).values())

        self.assertEqual(actual_data, expected_data)

    def test_get_expertise_none(self):
        response = self.client.get(self.expertise_url)

        actual_data = response.json()
        expected_data = []

        self.assertEqual(actual_data, expected_data)

    def test_list_skill_and_expertise(self):
        skills, skill_ids = self._create_skills(5)
        expertise, expertise_ids = self._create_expertise(skills)

        response = self.client.get(
            self.list_skill_and_expertise_url,
            data={"skills": f"{skill_ids}", "expertise": f"{expertise_ids}"},
        )

        actual_data = response.json()

        expected_data = []
        for exp in expertise:
            expected_data.append(
                {
                    "skill": exp.skill.name,
                    "expertise": exp.name,
                }
            )

        self.assertEqual(actual_data, expected_data)

    def test_list_and_expertise_none(self):
        response = self.client.get(self.list_skill_and_expertise_url)

        actual_data = response.json()
        expected_data = []

        self.assertEqual(actual_data, expected_data)


class SubmitFeedbackViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("submit-feedback")

    def test_submit_feedback_get(self):
        response = self.client.get(self.url)

        actual = response.content.decode("utf-8")
        expected = "Something went wrong"

        self.assertEqual(actual, expected)

    def test_submit_feedback_invalid_post(self):
        response = self.client.post(self.url, data={"message": "test message"})

        actual = response.content.decode("utf-8")
        expected = "Something went wrong"

        self.assertEqual(actual, expected)

    def test_submit_feedback_valid_post(self):
        person = PersonFactory()
        _ = StatusFactory(person=person)
        _ = PersonSkillFactory(person=person)
        auth_person = PersonFactory()

        self.client.force_login(auth_person.user)
        response = self.client.post(
            self.url,
            data={
                "message": "test message",
                "stars": 5,
                "feedback-recipient-username": person.user.username,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, reverse("portfolio", args=(person.user.username,))
        )


class TalentPortfolioViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        person_auth = PersonFactory()
        self.client.force_login(person_auth.user)

        self.person = PersonFactory()
        _ = StatusFactory(person=self.person)
        self.person_skill = PersonSkillFactory(person=self.person)
        self.url = reverse("portfolio", args=(self.person.user.username,))

    def test_get_request(self):
        from talent.forms import FeedbackForm
        from talent.services import FeedbackService

        response = self.client.get(self.url)

        actual = response.context_data
        expected = {
            "user": self.person.user,
            "photo_url": "/media/avatars/profile-empty.png",
            "person": self.person,
            "person_linkedin_link": "",
            "person_twitter_link": "",
            "status": self.person.status,
            "skills": self.person_skill.skill,
            "expertise": self.person_skill.expertise,
            "FeedbackService": FeedbackService,
            "can_leave_feedback": True,
        }

        # we dont' need to check form
        actual.pop("form")

        bounty_claims = actual.pop("bounty_claims")
        self.assertEqual(bounty_claims.count(), 0)

        received_feedbacks = actual.pop("received_feedbacks")
        self.assertEqual(received_feedbacks.count(), 0)

        self.assertEqual(actual, expected)


# TODO: write tests for _remove_picture method. It is not written since it was not urgent
class ProfileViewTest(TestCase):
    def setUp(self):
        self.person = PersonFactory()
        self.client = Client()
        self.client.force_login(self.person.user)
        self.url = reverse("profile", args=(self.person.user.pk,))

    def test_get_context_data(self):
        response = self.client.get(self.url)

        actual = response.context_data
        expected = {
            "person": self.person,
            "pk": self.person.pk,
            "photo_url": "/media/avatars/profile-empty.png",
            "requires_upload": True,
        }

        for key in expected.keys():
            self.assertEqual(actual.get(key), expected.get(key))

    def test_post_valid(self):
        skills = SkillFactory.create_batch(3)
        skill_ids = [skill.id for skill in skills]

        expertise = ExpertiseFactory.create_batch(5)
        expertise_ids = [exp.id for exp in expertise]

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
            "selected_skill_ids": f"{skill_ids}",
            "selected_expertise_ids": f"{expertise_ids}",
        }

        _ = self.client.post(self.url, data=data)

        person_skill = PersonSkill.objects.get(person=self.person)
        self.assertIsNotNone(person_skill)
        self.assertEqual(
            person_skill.skill,
            list(Skill.objects.filter(id__in=skill_ids).values_list("name", flat=True)),
        )
        self.assertEqual(
            person_skill.expertise,
            list(
                Expertise.objects.filter(id__in=expertise_ids).values_list(
                    "name", flat=True
                )
            ),
        )
