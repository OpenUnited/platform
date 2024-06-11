from model_bakery import baker

from e2e.base import BaseE2ETest
from e2e.pages.login_page import LoginPage


class TestLogin(BaseE2ETest):
    def setUp(self):
        super().setUp()
        self.page = self.browser.new_page()
        self.user_one = baker.make("security.User", username="testuser1", password="12345")
        self.user_one.set_password("12345")
        self.user_one.save()
        self.person = baker.make("talent.Person", user=self.user_one)

    def test_login(self):
        login_page = LoginPage(self.page)
        login_page.navigate(f"{self.live_server_url}{login_page.url}")
        login_page.login("testuser1", "12345")
        # self.assertTrue(self.page.is_visible("#navbar-menu-button"))
