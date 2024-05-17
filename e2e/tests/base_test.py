from playwright.sync_api import sync_playwright
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
import os

class PlaywrightBaseTest(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
        cls.playwright = sync_playwright().start()

    @classmethod
    def tearDownClass(cls):
        cls.playwright.stop()
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.browser = self.playwright.chromium.launch()

    def tearDown(self):
        self.browser.close()
        super().tearDown()
