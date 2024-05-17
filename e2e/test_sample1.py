# from e2e.tests.base_test import BaseE2ETest
# from security.tests.factories import UserFactory
# from talent.tests.factories import PersonFactory
# from .pages.login_page import LoginPage




# class PlaywrightTests1(BaseE2ETest):
#     def setUp(self):
#         self.user_one = UserFactory.create(username="testuser", password="12345")
#         self.user_one.set_password('12345')
#         self.user_one.save()
#         self.person = PersonFactory(user=self.user_one)

#     def tearDown(self):
#         self.browser.close()
#         self.playwright.stop()

#     def test_login_____1(self):
#         login_page = LoginPage(self.page)
#         login_page.navigate(f'{self.live_server_url}{login_page.url}')
#         login_page.login('testuser', '12345')
#         self.assertTrue(self.page.is_visible('#navbar-menu-button'))
