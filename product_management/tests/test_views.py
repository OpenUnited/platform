from django.test import TestCase, Client
from django.urls import reverse
from product_management.models import Challenge, Capability
from .factories import OwnedProductFactory, PersonFactory, ChallengeFactory


class CreateChallengeViewTestCase(TestCase):
    """
    docker-compose --env-file docker.env exec platform sh -c "python manage.py test product_management.tests.test_views.CreateChallengeViewTestCase"
    """

    def setUp(self):
        self.person = PersonFactory()
        self.product = OwnedProductFactory()
        self.client = Client()
        self.url = reverse("create-challenge")
        self.login_url = reverse("sign_in")

    def test_post(self):
        # Test login required
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"{self.login_url}?next={self.url}")
        # Test Challenge object creation
        self.client.force_login(self.person.user)
        data = {
            "title": "title challenge 1",
            "description": "desc challenge 1",
            "product": self.product.id,
            "priority": "0",
            "status": "2",
            "reward_type": Challenge.REWARD_TYPE[1][0],
        }
        res = self.client.post(self.url, data=data)
        instance = Challenge.objects.get(title=data["title"])
        self.assertEqual(res.status_code, 302)
        self.assertEqual(instance.created_by.id, self.person.id)
        self.assertEqual(instance.title, data["title"])
        self.assertEqual(instance.description, data["description"])
        self.assertEqual(instance.status, int(data["status"]))
        self.assertEqual(instance.priority, int(data["priority"]))
        self.assertEqual(instance.reward_type, data["reward_type"])
        self.assertEqual(
            res.url,
            reverse(
                "challenge_detail",
                args=(
                    instance.product.slug,
                    instance.id,
                ),
            ),
        )

    def tearDown(self):
        Challenge.objects.get(created_by=self.person).delete()


class CapabilityDetailViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.product = OwnedProductFactory()
        self.root_capability = Capability.add_root(
            name="capability name", description="capability description"
        )
        self.url = reverse(
            "capability_detail",
            args=(
                self.product.slug,
                self.root_capability.pk,
            ),
        )

    def test_get(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "product_management/capability_detail.html", response.template_name
        )
        self.assertEqual(response.context_data.get("challenges").count(), 0)

        challenge_count = 5
        self.challenge_list = [
            ChallengeFactory(capability=self.root_capability)
            for _ in range(challenge_count)
        ]

        response = self.client.get(self.url)
        self.assertEqual(
            response.context_data.get("challenges").count(), challenge_count
        )

        [ch.delete() for ch in self.challenge_list]

    def tearDown(self):
        self.root_capability.delete()
