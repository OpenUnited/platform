import re

from django.core import mail

from .base import BasePage


class SignupPage(BasePage):
    def __init__(self, page):
        super().__init__(page)

        self.url = "/sign-up/"

        self.fullname_field = self.page.locator("#id_0-full_name")
        self.email_field = self.page.locator("#id_0-email")
        self.preferred_name_field = self.page.locator("#id_0-preferred_name")
        self.send_verification_code_button = self.page.locator("#send-verification-code-btn")

        self.otp_field = self.page.locator("#id_1-verification_code")
        self.verify_code_btn = self.page.locator("#verify-code-btn")

        self.username_field = self.page.locator("#id_2-username")
        self.password_field = self.page.locator("#password-checker-field")
        self.password_confirm_field = self.page.locator("#id_2-password_confirm")
        self.signup_btn = self.page.locator("#signup-btn")

    def signup(self, fullname, email, preferred_name, username, password):
        # Step 1
        self.fullname_field.fill(fullname)
        self.email_field.fill(email)
        self.preferred_name_field.fill(preferred_name)
        self.send_verification_code_button.click()
        self.get_latest_otp()

        # Step 2
        otp = self.get_latest_otp()
        self.otp_field.fill(otp[0])
        for idx, digit in enumerate(otp[1:]):
            selector = f'input[id="id_1-verification_code"][style="--_otp-digit: {idx + 1};"]'
            self.page.wait_for_selector(selector)
            self.otp_field.type(digit)
            self.page.wait_for_timeout(100)
        self.verify_code_btn.click()

        # Step 3
        self.username_field.fill(username)
        self.password_field.fill(password)
        self.password_confirm_field.fill(password)
        self.signup_btn.click()

    def get_latest_otp(self):
        outbox = mail.outbox
        email_body = outbox[-1].body
        pattern = r"Code: (\d+)"
        matches = re.search(pattern, email_body)
        if matches:
            return matches.group(1)
