from django.test import TestCase, Client
from django.urls import reverse
from product_management.models import Challenge
from .factories import (
    OwnedProductFactory,
    PersonFactory
)



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
        self.assertEqual(res.url, reverse(
                "challenge_detail",
                args=(
                    instance.product.slug,
                    instance.id,
                ),
            ))

    
    def tearDown(self):
        Challenge.objects.get(created_by=self.person).delete()
        
