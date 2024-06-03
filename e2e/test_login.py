from e2e.base import BaseE2ETest

class TestLogin(BaseE2ETest):
    def setUp(self):
        super().setUp()


    def test_login(self):
        self.assertTrue(self.page.is_visible("#navbar-menu-button"))
