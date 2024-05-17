



from playwright.sync_api import sync_playwright
from e2e.pages.login_page import LoginPage
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from termcolor import cprint

import django
django.setup()



from security.tests.factories import UserFactory
import os


class PlaywrightTests1(StaticLiveServerTestCase):
    def setUp(self):
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
        self.playwright = sync_playwright().start()
        # self.browser = self.playwright.chromium.launch(headless=False, slow_mo=1000)
        self.browser = self.playwright.chromium.launch()
        self.page = self.browser.new_page()
        cprint(f'\n\n{self.live_server_url=}', "green")
        self.user_one = UserFactory.create(username="testuser", password="12345")
        self.user_one.set_password('12345')
        self.user_one.save()
        cprint(f'Created user: {self.user_one.username}, {self.user_one.password}', "green")
        from talent.tests.factories import PersonFactory
        self.person = PersonFactory(user=self.user_one)

    def tearDown(self):
        self.browser.close()
        self.playwright.stop()

    def test_login(self):
        login_page = LoginPage(self.page)
        login_page.navigate(f'{self.live_server_url}{login_page.url}')
        login_page.login('testuser', '12345')
        self.assertTrue(self.page.is_visible('#navbar-menu-button'))
