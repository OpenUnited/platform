import os
from e2e.pages.login_page import LoginPage
from model_bakery import baker

from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from playwright.sync_api import sync_playwright


class BaseE2ETest(StaticLiveServerTestCase):
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
        self.create_user()
        self.login_user()

    def tearDown(self):
        self.browser.close()
        super().tearDown()
    
    def login_user(self,):
        login_page = LoginPage(self.page)
        login_page.navigate(f"{self.live_server_url}{login_page.url}")
        login_page.login(self.username, self.password)
    

    def create_user(self):
        self.username = "testuser"
        self.password = "12345"

        first_name="Test"
        last_name="User"
        full_name = f'{first_name} {last_name}'

        
        self.page = self.browser.new_page()
        

        self.user_one = baker.make(
            "security.User",
            username=self.username,
            password=self.password,
            first_name=first_name,
            last_name=last_name,
        )
        self.user_one.set_password(self.password)
        self.user_one.save()
        self.person = baker.make("talent.Person", user=self.user_one, photo="image.png", full_name=full_name)
