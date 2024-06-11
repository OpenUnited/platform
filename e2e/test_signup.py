from e2e.base import BaseE2ETest
from e2e.pages.signup_page import SignupPage


class TestLogin(BaseE2ETest):
    def setUp(self):
        super().setUp()
        self.page = self.browser.new_page()

    def test_signup(self):
        signup_page = SignupPage(self.page)
        signup_page.navigate(f"{self.live_server_url}{signup_page.url}")
        signup_page.signup("Pacey Witter", "pacey@gmail.com", "pacey", "pacey", "4@Password")
        # self.assertTrue(self.page.is_visible("#navbar-menu-button"))
