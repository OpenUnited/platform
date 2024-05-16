from .base_page import BasePage

class LoginPage(BasePage):
    def __init__(self, page):
        super().__init__(page)
        self.username_field = self.page.locator("#username")
        self.password_field = self.page.locator("#password")
        self.login_button = self.page.locator("#login-button")

    def login(self, username, password):
        self.username_field.fill(username)
        self.password_field.fill(password)
        self.login_button.click()
