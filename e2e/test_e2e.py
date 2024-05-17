from playwright.sync_api import sync_playwright
from .pages.base_page import BasePage
from termcolor import cprint

class LoginPage(BasePage):
    def __init__(self, page):
        super().__init__(page)
        cprint(f'8',"green")
        self.username_field = self.page.locator("#username")
        self.password_field = self.page.locator("#password")
        self.login_button = self.page.locator("#login-button")

    def login(self, username, password):
        cprint(f'13',"green")
        self.username_field.fill(username)
        self.password_field.fill(password)
        self.login_button.click()




class TestSome:

    def test_login_with_valid_credentials(browser, django_server):
        """Test login functionality with valid credentials."""

        # ... Interact with the login page using browser and page methods
        # (e.g., navigate, fill form, submit, and assert successful login)
        page = browser.new_page()
        page.goto("http://localhost:8000/login")  # Access login page using the running server

        # ... (rest of your test logic using Playwright and page methods)

        page.close()

    # def test_login_with_invalid_credentials(browser, django_server):
    #     """Test login functionality with invalid credentials."""

    #     # ... (Similar structure as above test, using invalid credentials and asserting error messages)

    #     page.close()
