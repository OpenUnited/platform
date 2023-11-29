import os
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile

from openunited.tests.base import clean_up
from talent.models import BountyClaim
from product_management.models import (
    Product,
    Challenge,
    Capability,
    Idea,
    Bug,
    Attachment,
    Bounty,
)
from security.models import ProductRoleAssignment
from security.tests.factories import ProductRoleAssignmentFactory
from .factories import (
    OwnedProductFactory,
    PersonFactory,
    ChallengeFactory,
    SkillFactory,
    ExpertiseFactory,
    BountyFactory,
    BountyClaimFactory,
    ProductIdeaFactory,
    ProductBugFactory,
    AttachmentFactory,
)


class BaseTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.client = Client()
        self.login_url = reverse("sign_in")


class BaseProductTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.product = OwnedProductFactory()


class ChallengeListViewTest(BaseProductTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("challenges")

    def test_get_none(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "product_management/challenges.html", response.template_name
        )

        actual = response.context_data
        clean_up(actual, exclude=["object_list"])

        self.assertIsNotNone(actual.pop("request"))
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
        self.assertIn(
            "product_management/challenges.html", response.template_name
        )

        actual = response.context_data
        clean_up(actual)

        self.assertIsNotNone(actual.pop("request"))
        self.assertEqual(actual.pop("challenges").count(), 8)

        expected = {"is_paginated": True}
        self.assertDictEqual(actual, expected)

        response = self.client.get(f"{self.url}?page=2")
        self.assertEqual(response.status_code, 200)

        actual = response.context_data
        clean_up(actual)

        self.assertIsNotNone(actual.pop("request"))
        self.assertEqual(actual.pop("challenges").count(), 8)
        self.assertDictEqual(actual, expected)

        response = self.client.get(f"{self.url}?page=3")
        self.assertEqual(response.status_code, 200)

        actual = response.context_data
        clean_up(actual)

        self.assertIsNotNone(actual.pop("request"))
        self.assertEqual(actual.pop("challenges").count(), 4)
        self.assertDictEqual(actual, expected)


class ProductListViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("products")

    def test_get_none(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "product_management/products.html", response.template_name
        )
        self.assertFalse(response.context_data.get("is_paginated"))
        self.assertEqual(response.context_data.get("products").count(), 0)

    def test_get_some(self):
        _ = [OwnedProductFactory() for _ in range(12)]

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        actual = response.context_data
        clean_up(actual)

        products = Product.objects.all().order_by("created_at")

        self.assertQuerySetEqual(actual.pop("products"), products[:8])

        expected = {"is_paginated": True}
        self.assertDictEqual(actual, expected)

        response = self.client.get(f"{self.url}?page=2")
        self.assertEqual(response.status_code, 200)

        actual = response.context_data
        clean_up(actual)

        self.assertQuerySetEqual(actual.pop("products"), products[8:])

        expected = {"is_paginated": True}
        self.assertDictEqual(actual, expected)


class ProductRedirectViewTest(BaseProductTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("product_detail", args=(self.product.slug,))

    def test_get(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, reverse("product_summary", args=(self.product.slug,))
        )


class ProductSummaryViewTest(BaseProductTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("product_summary", args=(self.product.slug,))

    def test_get_none(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "product_management/product_summary.html", response.template_name
        )

        actual = response.context_data
        clean_up(actual)

        expected = {
            "product": self.product,
            "product_slug": self.product.slug,
            "can_edit_product": False,
        }

        self.assertQuerySetEqual(
            actual.pop("challenges"), Challenge.objects.none()
        )
        self.assertQuerySetEqual(
            actual.pop("capabilities"), Challenge.objects.none()
        )
        self.assertDictEqual(actual, expected)

    def test_get_some(self):
        for _ in range(0, 5):
            ChallengeFactory(
                product=self.product,
                status=Challenge.CHALLENGE_STATUS_AVAILABLE,
            )

        root_capability = Capability.add_root(
            name="dummy name", description="dummy description"
        )
        root_capability.product.add(self.product)

        # TODO: write one more case for this case
        self.client.force_login(self.product.content_object.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "product_management/product_summary.html", response.template_name
        )

        actual = response.context_data
        clean_up(actual)

        expected = {
            "product": self.product,
            "product_slug": self.product.slug,
            "can_edit_product": False,
        }

        self.assertQuerySetEqual(
            actual.pop("challenges"), Challenge.objects.all(), ordered=False
        )
        self.assertQuerySetEqual(
            actual.pop("capabilities"), Capability.objects.all(), ordered=False
        )
        self.assertDictEqual(actual, expected)

        _ = ProductRoleAssignmentFactory(
            person=self.product.content_object,
            product=self.product,
            role=ProductRoleAssignment.PRODUCT_ADMIN,
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data.get("can_edit_product"), True)


class CreateChallengeViewTest(BaseProductTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("create-challenge", args=(self.product.slug,))
        self.person = PersonFactory()

    def test_post_login_required(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"{self.login_url}?next={self.url}")

    def test_post_invalid(self):
        self.client.force_login(self.person.user)

        # "title" is missing
        expected = {
            "description": "desc challenge 1",
            "product": self.product.id,
            "reward_type": Challenge.REWARD_TYPE[1][0],
            "priority": 0,
            "status": 2,
        }

        response = self.client.post(self.url, data=expected)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "product_management/create_challenge.html", response.template_name
        )

        form = response.context_data.get("form")
        self.assertFalse(form.is_valid())
        self.assertEqual({"title": ["This field is required."]}, form.errors)

    def test_post_valid(self):
        self.client.force_login(self.person.user)

        images = [
            SimpleUploadedFile(
                "image_one.png", b"image_content", content_type="image/png"
            ),
            SimpleUploadedFile(
                "image_two.png", b"image_content", content_type="image/png"
            ),
        ]

        expected = {
            "title": "title challenge 1",
            "description": "desc challenge 1",
            "product": self.product.id,
            "reward_type": Challenge.REWARD_TYPE[1][0],
            "priority": 0,
            "status": 2,
            "attachment": images,
        }

        response = self.client.post(self.url, data=expected)
        self.assertEqual(response.status_code, 302)

        instance = Challenge.objects.get(title=expected["title"])
        self.assertEqual(instance.created_by.id, self.person.id)
        self.assertEqual(
            response.url,
            reverse(
                "challenge_detail",
                args=(
                    instance.product.slug,
                    instance.id,
                ),
            ),
        )

        actual = {
            "title": instance.title,
            "description": instance.description,
            "product": instance.product.id,
            "reward_type": instance.reward_type,
            "priority": instance.priority,
            "status": instance.status,
            "attachment": images,
        }

        self.assertDictEqual(actual, expected)

        Challenge.objects.get(created_by=self.person).delete()


class UpdateChallengeViewTest(BaseProductTestCase):
    def setUp(self):
        super().setUp()
        self.challenge = ChallengeFactory()
        self.person = PersonFactory()
        self.url = reverse(
            "update-challenge",
            args=(self.challenge.product.slug, self.challenge.id),
        )

    def test_post_login_required(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"{self.login_url}?next={self.url}")

    def test_post_valid(self):
        self.client.force_login(self.person.user)

        data = {
            "title": "updated title",
            "description": "updated description",
            "product": self.challenge.product.id,
            "reward_type": self.challenge.reward_type,
            "priority": self.challenge.priority,
            "status": self.challenge.status,
        }
        response = self.client.post(self.url, data=data)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse(
                "challenge_detail",
                args=(self.challenge.product.slug, self.challenge.id),
            ),
        )

        self.challenge.refresh_from_db()
        self.assertEqual(self.challenge.title, data.get("title"))
        self.assertEqual(self.challenge.description, data.get("description"))


class DeleteChallengeViewTest(BaseProductTestCase):
    def setUp(self):
        super().setUp()
        self.challenge = ChallengeFactory()
        self.person = PersonFactory()
        self.url = reverse(
            "delete-challenge",
            args=(self.challenge.product.slug, self.challenge.id),
        )

    def test_post_login_required(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"{self.login_url}?next={self.url}")

    def test_delete_without_permission(self):
        self.client.force_login(self.person.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse(
                "challenge_detail",
                args=(
                    self.challenge.product.slug,
                    self.challenge.pk,
                ),
            ),
        )

        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn(
            "You do not have rights to remove this challenge.", messages
        )

    def test_delete_with_permission_one(self):
        self.client.force_login(self.person.user)

        _ = ProductRoleAssignmentFactory(
            person=self.person,
            product=self.challenge.product,
            role=ProductRoleAssignment.PRODUCT_ADMIN,
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse("challenges"),
        )

        with self.assertRaises(Challenge.DoesNotExist):
            self.challenge.refresh_from_db()

        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("The challenge is successfully deleted!", messages)

    def test_delete_with_permission_two(self):
        self.client.force_login(self.person.user)

        challenge = ChallengeFactory(created_by=self.person)
        url = reverse(
            "delete-challenge",
            args=(challenge.product.slug, challenge.id),
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("challenges"))

        with self.assertRaises(Challenge.DoesNotExist):
            challenge.refresh_from_db()

        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("The challenge is successfully deleted!", messages)


class CapabilityDetailViewTest(BaseProductTestCase):
    def setUp(self):
        super().setUp()
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


class ChallengeDetailViewTest(BaseProductTestCase):
    def setUp(self):
        super().setUp()
        self.person = PersonFactory()
        self.challenge = ChallengeFactory(created_by=self.person)
        self.url = reverse(
            "challenge_detail",
            args=(self.challenge.product.slug, self.challenge.pk),
        )

    def test_get_anon(self):
        response = self.client.get(self.url)
        self.assertIn(
            "product_management/challenge_detail.html", response.template_name
        )

        actual = response.context_data
        clean_up(actual, extra=["bounty_claim_form"])

        expected = {
            "product": self.challenge.product,
            "product_slug": self.challenge.product.slug,
            "actions_available": False,
            "bounty": None,
            "bounty_claim": None,
            "challenge": self.challenge,
            "current_user_created_claim_request": False,
            "is_claimed": False,
        }
        self.assertDictEqual(actual, expected)

    def test_get_auth(self):
        self.client.force_login(user=self.person.user)

        response = self.client.get(self.url)
        self.assertIn(
            "product_management/challenge_detail.html", response.template_name
        )

        actual = response.context_data
        clean_up(actual, extra=["bounty_claim_form"])

        expected = {
            "product": self.challenge.product,
            "product_slug": self.challenge.product.slug,
            "actions_available": True,
            "challenge": self.challenge,
            "bounty": None,
            "bounty_claim": None,
            "current_user_created_claim_request": False,
            "is_claimed": False,
        }
        self.assertDictEqual(actual, expected)

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

        actual = response.context_data
        clean_up(actual, extra=["bounty_claim_form"])

        expected = {
            "product": challenge.product,
            "product_slug": challenge.product.slug,
            "challenge": challenge,
            "bounty": b_one,
            "bounty_claim": bc_one,
            "current_user_created_claim_request": False,
            "actions_available": False,
            "is_claimed": True,
            "claimed_by": bc_one.person,
        }
        self.assertDictContainsSubset(actual, expected)

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

        actual = response.context_data
        clean_up(actual, extra=["bounty_claim_form"])

        expected = {
            "product": challenge.product,
            "product_slug": challenge.product.slug,
            "challenge": challenge,
            "bounty": b_one,
            "bounty_claim": bc_one,
            "current_user_created_claim_request": True,
            "actions_available": False,
            "is_claimed": True,
            "claimed_by": bc_one.person,
        }
        self.assertDictEqual(actual, expected)


class CreateProductBugTest(BaseProductTestCase):
    def setUp(self):
        super().setUp()
        self.person = PersonFactory()
        self.url = reverse("add_product_bug", args=(self.product.slug,))

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


class ProductBugDetailViewTest(BaseProductTestCase):
    def setUp(self):
        super().setUp()
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


class UpdateProductBugViewTest(BaseProductTestCase):
    def setUp(self):
        super().setUp()
        self.bug = ProductBugFactory()
        self.person = PersonFactory()
        self.url = reverse(
            "update_product_bug", args=(self.bug.product.slug, self.bug.id)
        )

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


class ProductIdeasAndBugsViewTest(BaseProductTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("product_ideas_bugs", args=(self.product.slug,))

    def test_get_context_data_none(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "product_management/product_ideas_and_bugs.html",
            response.template_name,
        )

        actual = response.context_data
        clean_up(actual)

        self.assertQuerySetEqual(actual.pop("ideas"), Idea.objects.none())
        self.assertQuerySetEqual(actual.pop("bugs"), Bug.objects.none())

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
        clean_up(actual)

        self.assertQuerySetEqual(
            actual.pop("ideas"), Idea.objects.all(), ordered=False
        )
        self.assertQuerySetEqual(
            actual.pop("bugs"), Bug.objects.all(), ordered=False
        )

        expected = {
            "product_slug": self.product.slug,
            "product": self.product,
        }

        self.assertDictEqual(expected, actual)


class ProductIdeaListViewTest(BaseProductTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("product_idea_list", args=(self.product.slug,))

    def test_get_queryset(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "product_management/product_idea_list.html", response.template_name
        )

        actual = response.context_data
        clean_up(actual)

        self.assertQuerySetEqual(actual.pop("ideas"), Idea.objects.none())

        expected = {
            "product": self.product,
            "product_slug": self.product.slug,
            "is_paginated": False,
        }
        self.assertDictEqual(actual, expected)


class ProductBugListViewTest(BaseProductTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("product_bug_list", args=(self.product.slug,))

    def test_get_queryset(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "product_management/product_bug_list.html", response.template_name
        )

        actual = response.context_data
        clean_up(actual)

        self.assertQuerySetEqual(actual.pop("bugs"), Bug.objects.none())

        expected = {
            "is_paginated": False,
            "product": self.product,
            "product_slug": self.product.slug,
        }
        self.assertDictEqual(actual, expected)


class DeleteAttachmentViewTest(BaseProductTestCase):
    def setUp(self):
        super().setUp()
        self.challenge = ChallengeFactory(
            created_by=self.product.content_object
        )
        self.attachment_one = AttachmentFactory()
        self.challenge.attachment.add(self.attachment_one)
        self.url = reverse(
            "delete-attachment",
            args=(self.attachment_one.id,),
        )

    def test_get_anon(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            f"{self.login_url}?next=/attachment/delete/{self.attachment_one.id}",
        )

    def test_get_auth(self):
        self.client.force_login(self.product.content_object.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            f"/{self.challenge.product.slug}/challenge/{self.challenge.id}",
        )

        # add test to make sure the request owner has rights to delete the image(s)
        with self.assertRaises(Attachment.DoesNotExist):
            self.attachment_one.refresh_from_db()


class CreateBountyViewTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.challenge = ChallengeFactory()
        self.url = reverse(
            "create-bounty",
            args=(
                self.challenge.product.slug,
                self.challenge.pk,
            ),
        )
        self.person = PersonFactory()
        self.success_url = reverse(
            "challenge_detail",
            args=(self.challenge.product.slug, self.challenge.pk),
        )

    def test_anon(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{self.login_url}?next={self.url}")

    def test_get_auth(self):
        self.client.force_login(self.person.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "product_management/create_bounty.html", response.template_name
        )

    def test_invalid_post(self):
        self.client.force_login(self.person.user)

        # challenge, skill and expertise are missing
        data = {
            "points": 10,
            "status": 2,
            "is_active": True,
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)

        form = response.context_data.get("form")
        self.assertFalse(form.is_valid())

    def test_post(self):
        self.client.force_login(self.person.user)

        skill = SkillFactory()
        expertise_one = ExpertiseFactory(skill=skill)
        expertise_two = ExpertiseFactory(skill=skill)

        data = {
            "challenge": self.challenge.id,
            "selected_skill_ids": f"[{skill.id}]",
            "selected_expertise_ids": f"[{expertise_one.id}, {expertise_two.id}]",
            "points": 10,
            "status": 2,
            "is_active": True,
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.success_url)

        self.challenge.refresh_from_db()

        bounties = self.challenge.bounty_set.all()
        self.assertNotEqual(bounties.count(), 0)

        bounty = bounties.last()
        self.assertEqual(bounty.points, data.get("points"))
        self.assertEqual(bounty.status, data.get("status"))
        self.assertEqual(bounty.is_active, data.get("is_active"))
        self.assertEqual(bounty.skill, skill)
        self.assertEqual(bounty.expertise.count(), 2)

        skill.delete()
        expertise_one.delete()
        expertise_two.delete()


class UpdateBountyViewTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.challenge = ChallengeFactory()
        self.bounty = BountyFactory(challenge=self.challenge)
        self.url = reverse(
            "update-bounty",
            args=(
                self.challenge.product.slug,
                self.challenge.id,
                self.bounty.id,
            ),
        )
        self.person = PersonFactory()
        self.success_url = reverse(
            "challenge_detail",
            args=(
                self.challenge.product.slug,
                self.challenge.id,
            ),
        )

    def test_anon(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{self.login_url}?next={self.url}")

    def test_get(self):
        self.client.force_login(self.person.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "product_management/update_bounty.html", response.template_name
        )

    def test_invalid_post(self):
        self.client.force_login(self.person.user)

        # challenge, skill and expertise are missing
        data = {
            "points": 10,
            "status": 2,
            "is_active": True,
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)

        form = response.context_data.get("form")
        self.assertFalse(form.is_valid())
        self.assertListEqual(
            form.errors.get("challenge"), ["This field is required."]
        )
        self.assertListEqual(
            form.errors.get("selected_skill_ids"), ["This field is required."]
        )
        self.assertListEqual(
            form.errors.get("selected_expertise_ids"),
            ["This field is required."],
        )

    def test_post(self):
        self.client.force_login(self.person.user)

        skill = SkillFactory()
        expertise_one = ExpertiseFactory(skill=skill)
        expertise_two = ExpertiseFactory(skill=skill)

        data = {
            "challenge": self.challenge.id,
            "selected_skill_ids": f"[{skill.id}]",
            "selected_expertise_ids": f"[{expertise_one.id}, {expertise_two.id}]",
            "points": self.bounty.points + 20,
            "status": 4,
            "is_active": False,
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.success_url)

        self.bounty.refresh_from_db()

        self.assertEqual(self.bounty.points, data.get("points"))
        self.assertEqual(self.bounty.status, data.get("status"))
        self.assertFalse(data.get("is_active"))

        skill.delete()
        expertise_one.delete()
        expertise_two.delete()


class DeleteBountyViewTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.bounty = BountyFactory()
        challenge = self.bounty.challenge
        self.url = reverse(
            "delete-bounty",
            args=(
                challenge.product.slug,
                challenge.id,
                self.bounty.id,
            ),
        )
        self.success_url = reverse("challenges")
        self.person = PersonFactory()

    def test_anon(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{self.login_url}?next={self.url}")

    def test_get(self):
        self.client.force_login(self.person.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("challenges"))

        with self.assertRaises(Bounty.DoesNotExist):
            self.bounty.refresh_from_db()
