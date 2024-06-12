from e2e.pages.base import BasePage


class LoginPage(BasePage):
    def __init__(self, page):
        super().__init__(page)
        self.url = "/sign-in/"
        self.username_field = self.page.locator("#id_username_or_email")
        self.password_field = self.page.locator("#id_password")
        self.login_button = self.page.locator("#sign-in-button")

    def login(self, username, password):
        self.username_field.fill(username)
        self.password_field.fill(password)
        self.login_button.click()
