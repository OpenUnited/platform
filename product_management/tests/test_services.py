from django.test import TestCase

from product_management.services import ProductService


class ProductServiceTest(TestCase):
    def test_convert_youtube_link_to_embed(self):
        self.assertEqual(
            ProductService.convert_youtube_link_to_embed(""), None
        )
        self.assertEqual(
            ProductService.convert_youtube_link_to_embed(
                "https://www.youtube.com/watch?v=HlgG395PQWw"
            ),
            "https://www.youtube.com/embed/HlgG395PQWw",
        )
