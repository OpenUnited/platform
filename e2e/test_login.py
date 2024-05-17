from e2e.pages.login_page import LoginPage
from talent.tests.factories import PersonFactory
from security.tests.factories import UserFactory
from e2e.base_test import PlaywrightBaseTest

class TestPlaywrightTests1(PlaywrightBaseTest):
    def setUp(self):
        super().setUp()
        self.page = self.browser.new_page() 
        self.user_one = UserFactory.create(username="testuser", password="12345")
        self.user_one.set_password('12345')
        self.user_one.save()
        self.person = PersonFactory(user=self.user_one)

    def test_login(self):
        login_page = LoginPage(self.page)
        login_page.navigate(f'{self.live_server_url}{login_page.url}')
        login_page.login('testuser', '12345')
        self.assertTrue(self.page.is_visible('#navbar-menu-button'))
