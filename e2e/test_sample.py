from e2e.pages.login_page import LoginPage
from talent.tests.factories import PersonFactory
from security.tests.factories import UserFactory
from termcolor import cprint
from .tests.base_test import PlaywrightBaseTest

class TestPlaywrightTests1(PlaywrightBaseTest):
    def setUp(self):
        super().setUp()
        self.page = self.browser.new_page()  # Initialize the page attribute
        self.user_one = UserFactory.create(username="testuser", password="12345")
        self.user_one.set_password('12345')
        self.user_one.save()
        cprint(f'Created user: {self.user_one.username}, {self.user_one.password}', "green")
        self.person = PersonFactory(user=self.user_one)

    def test_login(self):
        login_page = LoginPage(self.page)
        login_page.navigate(f'{self.live_server_url}{login_page.url}')
        login_page.login('testuser', '12345')
        self.assertTrue(self.page.is_visible('#navbar-menu-button'))
