import os
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from talent.models import Status
from .factories import PersonFactory


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
        self.person_with_photo = PersonFactory(photo=create_image("test_image.jpg"))

    def test_get_photo_url(self):
        actual_url, requires_upload = self.person.get_photo_url()
        expected_url = "/media/avatars/profile-empty.png"

        self.assertEqual(actual_url, expected_url)
        self.assertTrue(requires_upload)

        actual_url, requires_upload = self.person_with_photo.get_photo_url()
        expected_url = self.person_with_photo.photo.url

        self.assertEqual(actual_url, expected_url)
        self.assertFalse(requires_upload)

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
    def test_get_display_points(self):
        self.assertEqual(Status.get_display_points(Status.DRONE), "< 50")
        self.assertEqual(Status.get_display_points(Status.HONEYBEE), "< 500")
        self.assertEqual(Status.get_display_points(Status.TRUSTED_BEE), "< 2000")
        self.assertEqual(Status.get_display_points(Status.QUEEN_BEE), "< 8000")
        self.assertEqual(Status.get_display_points(Status.BEEKEEPER), ">= 8000")
