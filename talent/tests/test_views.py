from django.test import TestCase, Client
from django.urls import reverse

from talent.models import Skill, Expertise
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
