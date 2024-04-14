import os
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
import factory

from talent import signals
from talent.models import Status, BountyClaim
from .factories import PersonFactory, StatusFactory
from product_management.tests.factories import (
    BountyClaimFactory,
    BountyFactory,
)


def create_image(image_name):
    image = Image.new("RGB", (100, 100))
    image_path = f"/tmp/{image_name}"
    image.save(image_path)
    file = open(image_path, "rb")
    image = SimpleUploadedFile(
        name=image_name, content=file.read(), content_type="image/jpeg"
    )
    file.close()
    os.remove(file.name)
    return image


class PersonModelTest(TestCase):
    def setUp(self):
        self.person = PersonFactory()
        self.person_with_photo = PersonFactory(
            photo=create_image("test_image.jpg")
        )

    def test_get_photo_url(self):
        actual_url = self.person.get_photo_url()
        expected_url = "/media/avatars/profile-empty.png"

        self.assertEqual(actual_url, expected_url)

        actual_url = self.person_with_photo.get_photo_url()
        expected_url = self.person_with_photo.photo.url

        self.assertEqual(actual_url, expected_url)

        os.remove(self.person_with_photo.photo.path)

    def test_delete_photo(self):
        self.assertTrue(os.path.exists(self.person_with_photo.photo.path))

        self.person_with_photo.delete_photo()
        self.assertFalse(self.person_with_photo.photo)

    def test_toggle_bounties(self):
        self.assertTrue(self.person.send_me_bounties)
        self.person.toggle_bounties()
        self.assertFalse(self.person.send_me_bounties)
        self.person.toggle_bounties()
        self.assertTrue(self.person.send_me_bounties)


class StatusModelTest(TestCase):
    @factory.django.mute_signals(signals.post_save)
    def setUp(self):
        self.status = StatusFactory(points=200)

    def test_get_display_points(self):
        self.assertEqual(Status.get_display_points(Status.DRONE), "< 50")
        self.assertEqual(Status.get_display_points(Status.HONEYBEE), "< 500")
        self.assertEqual(
            Status.get_display_points(Status.TRUSTED_BEE), "< 2000"
        )
        self.assertEqual(Status.get_display_points(Status.QUEEN_BEE), "< 8000")
        self.assertEqual(
            Status.get_display_points(Status.BEEKEEPER), ">= 8000"
        )

    def test_get_status_from_points(self):
        self.assertEqual(self.status.get_status_from_points(), Status.HONEYBEE)
        self.assertEqual(self.status.get_status_from_points(10), Status.DRONE)
        self.assertEqual(self.status.get_status_from_points(49), Status.DRONE)
        self.assertEqual(
            self.status.get_status_from_points(50), Status.HONEYBEE
        )
        self.assertEqual(
            self.status.get_status_from_points(499), Status.HONEYBEE
        )
        self.assertEqual(
            self.status.get_status_from_points(500), Status.TRUSTED_BEE
        )
        self.assertEqual(
            self.status.get_status_from_points(1999), Status.TRUSTED_BEE
        )
        self.assertEqual(
            self.status.get_status_from_points(2_000), Status.QUEEN_BEE
        )
        self.assertEqual(
            self.status.get_status_from_points(7999), Status.QUEEN_BEE
        )
        self.assertEqual(
            self.status.get_status_from_points(8_000), Status.BEEKEEPER
        )
        self.assertEqual(
            self.status.get_status_from_points(100_00), Status.BEEKEEPER
        )


class BountyClaimTest(TestCase):
    def setUp(self):
        self.bounty_one = BountyFactory(points=20)
        self.claim_one = BountyClaimFactory(
            bounty=self.bounty_one, status=BountyClaim.ClaimStatus.GRANTED
        )

        self.bounty_two = BountyFactory(points=100)
        self.claim_two = BountyClaimFactory(
            bounty=self.bounty_two, status=BountyClaim.ClaimStatus.GRANTED
        )

        self.person = PersonFactory()
        self.bounty_three = BountyFactory(points=49)
        self.claim_three = BountyClaimFactory(
            person=self.person,
            bounty=self.bounty_three,
            status=BountyClaim.ClaimStatus.GRANTED,
        )

        self.bounty_four = BountyFactory(points=100)
        self.claim_four = BountyClaimFactory(
            person=self.person,
            bounty=self.bounty_four,
            status=BountyClaim.ClaimStatus.GRANTED,
        )

    def test_save_one(self):
        status = Status.objects.get(person=self.claim_one.person)
        self.claim_one.save()

        self.assertEqual(status.name, Status.DRONE)
        self.assertEqual(status.points, 0)

        self.claim_one.status = BountyClaim.ClaimStatus.COMPLETED
        self.claim_one.save()

        status.refresh_from_db()

        self.assertEqual(status.name, Status.DRONE)
        self.assertEqual(status.points, 20)

    def test_save_two(self):
        status = Status.objects.get(person=self.claim_two.person)
        self.claim_two.save()

        self.assertEqual(status.name, Status.DRONE)
        self.assertEqual(status.points, 0)

        self.claim_two.status = BountyClaim.ClaimStatus.COMPLETED
        self.claim_two.save()

        status.refresh_from_db()

        self.assertEqual(status.name, Status.HONEYBEE)
        self.assertEqual(status.points, 100)

    def test_save_three(self):
        status = Status.objects.get(person=self.person)

        self.assertEqual(status.name, Status.DRONE)
        self.assertEqual(status.points, 0)

        self.claim_three.status = BountyClaim.ClaimStatus.COMPLETED
        self.claim_three.save()

        status.refresh_from_db()

        self.assertEqual(status.name, Status.DRONE)
        self.assertEqual(status.points, 49)

        self.claim_four.status = BountyClaim.ClaimStatus.COMPLETED
        self.claim_four.save()

        status.refresh_from_db()

        self.assertEqual(status.name, Status.HONEYBEE)
        self.assertEqual(status.points, 149)
