from django.test import TestCase, Client
from django.test.client import RequestFactory
from django.urls import reverse

from talent.models import BountyClaim
from product_management.models import Challenge, Capability, Idea, Bug
from security.models import ProductRoleAssignment
from security.tests.factories import ProductRoleAssignmentFactory
from .factories import (
    OwnedProductFactory,
    PersonFactory,
    ChallengeFactory,
    BountyFactory,
    BountyClaimFactory,
    ProductIdeaFactory,
    ProductBugFactory,
)


class ChallengeListViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("challenges")

    def test_get_none(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        actual = response.context_data

        self.assertIsNotNone(actual.pop("request"))

        # don't need them
        actual.pop("paginator")
        actual.pop("page_obj")
        actual.pop("view")

        self.assertQuerySetEqual(
            actual.pop("challenges"), Challenge.objects.none()
        )
        self.assertQuerySetEqual(
            actual.pop("object_list"), Challenge.objects.none()
        )

        expected = {"is_paginated": False}

        self.assertDictEqual(actual, expected)

    def test_get_some(self):
        _ = [
            ChallengeFactory(status=Challenge.CHALLENGE_STATUS_DRAFT)
            for _ in range(0, 4)
        ]
        _ = [
            ChallengeFactory(status=Challenge.CHALLENGE_STATUS_BLOCKED)
            for _ in range(0, 4)
        ]
        _ = [
            ChallengeFactory(status=Challenge.CHALLENGE_STATUS_AVAILABLE)
            for _ in range(0, 4)
        ]
        _ = [
            ChallengeFactory(status=Challenge.CHALLENGE_STATUS_CLAIMED)
            for _ in range(0, 4)
        ]
        _ = [
            ChallengeFactory(status=Challenge.CHALLENGE_STATUS_DONE)
            for _ in range(0, 4)
        ]
        _ = [
            ChallengeFactory(status=Challenge.CHALLENGE_STATUS_IN_REVIEW)
            for _ in range(0, 4)
        ]

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        actual = response.context_data

        self.assertIsNotNone(actual.pop("request"))

        # don't need them
        actual.pop("paginator")
        actual.pop("page_obj")
        actual.pop("view")
        actual.pop("object_list")

        self.assertEqual(actual.pop("challenges").count(), 8)

        expected = {"is_paginated": True}
        self.assertDictEqual(actual, expected)

        response = self.client.get(f"{self.url}?page=2")
        self.assertEqual(response.status_code, 200)

        actual = response.context_data

        self.assertIsNotNone(actual.pop("request"))

        # don't need them
        actual.pop("paginator")
        actual.pop("page_obj")
        actual.pop("view")
        actual.pop("object_list")

        self.assertEqual(actual.pop("challenges").count(), 8)
        self.assertDictEqual(actual, expected)

        response = self.client.get(f"{self.url}?page=3")
        self.assertEqual(response.status_code, 200)

        actual = response.context_data

        self.assertIsNotNone(actual.pop("request"))

        # don't need them
        actual.pop("paginator")
        actual.pop("page_obj")
        actual.pop("view")
        actual.pop("object_list")

        self.assertEqual(actual.pop("challenges").count(), 4)
        self.assertDictEqual(actual, expected)


class ProductListViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("products")

    def test_get(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context_data.get("is_paginated"))
        self.assertEqual(response.context_data.get("products").count(), 0)

        _ = [OwnedProductFactory() for _ in range(12)]

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        # self.assertTrue(response.context_data.get("is_paginated"))
        self.assertEqual(response.context_data.get("products").count(), 12)

        # response = self.client.get(f"{self.url}?page=2")

        # self.assertEqual(response.status_code, 200)
        # self.assertTrue(response.context_data.get("is_paginated"))
        # self.assertEqual(response.context_data.get("products").count(), 4)


class ProductRedirectViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.product = OwnedProductFactory()
        self.url = reverse("product_detail", args=(self.product.slug,))

    def test_get(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, reverse("product_summary", args=(self.product.slug,))
        )


class ProductSummaryViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.product = OwnedProductFactory()
        self.url = reverse("product_summary", args=(self.product.slug,))

    def test_get(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data.get("product"), self.product)
        self.assertEqual(response.context_data.get("challenges").count(), 0)
        self.assertEqual(response.context_data.get("capabilities").count(), 0)
        self.assertEqual(response.context_data.get("can_edit_product"), False)

        _ = [
            ChallengeFactory(
                product=self.product,
                status=Challenge.CHALLENGE_STATUS_AVAILABLE,
            )
            for _ in range(0, 5)
        ]

        root_capability = Capability.add_root(
            name="dummy name", description="dummy description"
        )
        root_capability.product.add(self.product)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data.get("product"), self.product)
        self.assertEqual(response.context_data.get("challenges").count(), 5)
        self.assertEqual(response.context_data.get("capabilities").count(), 1)
        self.assertEqual(response.context_data.get("can_edit_product"), False)

        _ = ProductRoleAssignmentFactory(
            person=self.product.content_object,
            product=self.product,
            role=ProductRoleAssignment.PRODUCT_ADMIN,
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data.get("can_edit_product"), True)


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


class ChallengeDetailViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.person = PersonFactory()
        self.challenge = ChallengeFactory(created_by=self.person)
        self.url = reverse(
            "challenge_detail",
            args=(self.challenge.product.slug, self.challenge.pk),
        )

    def test_get_anon(self):
        response = self.client.get(self.url)

        expected_data = {
            "actions_available": False,
            "bounty": None,
            "bounty_claim": None,
            "challenge": self.challenge,
            "current_user_created_claim_request": False,
            "is_claimed": False,
        }
        self.assertDictContainsSubset(expected_data, response.context_data)

    def test_get_auth(self):
        self.client.force_login(user=self.person.user)

        response = self.client.get(self.url)

        expected_data = {
            "actions_available": True,
            "challenge": self.challenge,
            "bounty": None,
            "bounty_claim": None,
            "current_user_created_claim_request": False,
            "is_claimed": False,
        }
        self.assertDictContainsSubset(expected_data, response.context_data)

    def test_get_with_bounties(self):
        challenge = ChallengeFactory()
        url = reverse(
            "challenge_detail",
            args=(
                challenge.product.slug,
                challenge.pk,
            ),
        )

        b_one = BountyFactory(challenge=challenge)
        b_two = BountyFactory(challenge=challenge)
        bc_one = BountyClaimFactory(
            bounty=b_one, kind=BountyClaim.CLAIM_TYPE_ACTIVE
        )
        _ = BountyClaimFactory(
            bounty=b_one, kind=BountyClaim.CLAIM_TYPE_ACTIVE
        )
        _ = BountyClaimFactory(
            bounty=b_two, kind=BountyClaim.CLAIM_TYPE_ACTIVE
        )

        response = self.client.get(url)

        expected_data = {
            "challenge": challenge,
            "bounty": b_one,
            "bounty_claim": bc_one,
            "current_user_created_claim_request": False,
            "actions_available": False,
            "is_claimed": True,
            "claimed_by": bc_one.person,
        }
        self.assertDictContainsSubset(expected_data, response.context_data)

    def test_get_with_bounties_auth(self):
        self.client.force_login(self.person.user)

        challenge = ChallengeFactory()
        url = reverse(
            "challenge_detail",
            args=(
                challenge.product.slug,
                challenge.pk,
            ),
        )

        b_one = BountyFactory(challenge=challenge)
        b_two = BountyFactory(challenge=challenge)
        bc_one = BountyClaimFactory(
            bounty=b_one,
            person=self.person,
            kind=BountyClaim.CLAIM_TYPE_ACTIVE,
        )
        _ = BountyClaimFactory(
            bounty=b_one, kind=BountyClaim.CLAIM_TYPE_ACTIVE
        )
        _ = BountyClaimFactory(
            bounty=b_two, kind=BountyClaim.CLAIM_TYPE_ACTIVE
        )

        response = self.client.get(url)

        expected_data = {
            "challenge": challenge,
            "bounty": b_one,
            "bounty_claim": bc_one,
            "current_user_created_claim_request": True,
            "actions_available": False,
            "is_claimed": True,
            "claimed_by": bc_one.person,
        }
        self.assertDictContainsSubset(expected_data, response.context_data)


class CreateProductBugTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.product = OwnedProductFactory()
        self.person = PersonFactory()
        self.url = reverse("add_product_bug", args=(self.product.slug,))
        self.login_url = reverse("sign_in")

    def test_post(self):
        # Test login required
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"{self.login_url}?next={self.url}")

        # Test Bug object creation
        self.client.force_login(self.person.user)
        data = {
            "title": "Bug",
            "description": "Bug Description",
            "product": self.product,
            "person": self.person,
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse(
                "product_ideas_bugs",
                args=(self.product.slug,),
            ),
        )
        self.assertGreater(Bug.objects.filter(person=self.person).count(), 0)


class ProductBugDetailViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.bug = ProductBugFactory()
        self.url = reverse(
            "product_bug_detail", args=(self.bug.product.slug, self.bug.id)
        )

    def test_get(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "product_management/product_bug_detail.html",
            response.template_name,
        )


class UpdateProductBugViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.bug = ProductBugFactory()
        self.product = OwnedProductFactory()
        self.person = PersonFactory()
        self.url = reverse(
            "update_product_bug", args=(self.bug.product.slug, self.bug.id)
        )
        self.login_url = reverse("sign_in")

    def test_post(self):
        # Test login required
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"{self.login_url}?next={self.url}")

        # Test Feedback object update
        self.client.force_login(self.person.user)
        data = {
            "title": "Update Bug",
            "description": "Update Bug Description",
            "product": self.bug.product,
            "person": self.bug.person,
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse(
                "product_bug_detail", args=(self.bug.product.slug, self.bug.id)
            ),
        )

        obj = Bug.objects.get(pk=self.bug.pk)
        self.assertEqual(obj.title, data.get("title"))
        self.assertEqual(obj.description, data.get("description"))


class ProductIdeasAndBugsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.product = OwnedProductFactory()
        self.url = reverse("product_ideas_bugs", args=(self.product.slug,))

    def test_get_context_data_none(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        actual = response.context_data

        # don't need it
        actual.pop("view")

        actual_ideas = actual.pop("ideas")
        actual_bugs = actual.pop("bugs")
        self.assertQuerySetEqual(actual_ideas, Idea.objects.none())
        self.assertQuerySetEqual(actual_bugs, Bug.objects.none())

        expected = {
            "product_slug": self.product.slug,
            "product": self.product,
        }

        self.assertDictEqual(expected, actual)

    def test_get_context_data(self):
        [ProductIdeaFactory(product=self.product) for _ in range(0, 5)]
        [ProductBugFactory(product=self.product) for _ in range(0, 3)]

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        actual = response.context_data

        # don't need it
        actual.pop("view")

        actual_ideas = actual.pop("ideas")
        actual_bugs = actual.pop("bugs")
        self.assertQuerySetEqual(
            actual_ideas, Idea.objects.all(), ordered=False
        )
        self.assertQuerySetEqual(actual_bugs, Bug.objects.all(), ordered=False)

        expected = {
            "product_slug": self.product.slug,
            "product": self.product,
        }

        self.assertDictEqual(expected, actual)


class ProductIdeaListViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.product = OwnedProductFactory()
        self.url = reverse("product_idea_list", args=(self.product.slug,))

    def test_get_queryset(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        actual = response.context_data

        # don't need them
        actual.pop("paginator")
        actual.pop("page_obj")
        actual.pop("is_paginated")
        actual.pop("view")
        actual.pop("object_list")

        actual_ideas = actual.pop("ideas")
        self.assertQuerySetEqual(actual_ideas, Idea.objects.none())

        expected = {
            "product": self.product,
            "product_slug": self.product.slug,
        }
        self.assertDictEqual(actual, expected)


class ProductBugListViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.product = OwnedProductFactory()
        self.url = reverse("product_bug_list", args=(self.product.slug,))

    def test_get_queryset(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        actual = response.context_data

        # don't need them
        actual.pop("paginator")
        actual.pop("page_obj")
        actual.pop("is_paginated")
        actual.pop("view")
        actual.pop("object_list")

        actual_bugs = actual.pop("bugs")
        self.assertQuerySetEqual(actual_bugs, Bug.objects.none())

        expected = {
            "product": self.product,
            "product_slug": self.product.slug,
        }
        self.assertDictEqual(actual, expected)
