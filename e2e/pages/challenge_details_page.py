from e2e.pages.base import BasePage


class ChallengeDetailPage(BasePage):
    def __init__(self, page):
        super().__init__(page)
        self.bounty_add_btn = self.page.locator("#bounty-add-btn")
        self.expected_submission_date = self.page.locator("#expected_submission_date")
        self.terms_check_box = self.page.locator("#is_agreement_accepted")
        self.request_claim_button = self.page.locator('button[class="ajs-button ajs-ok"]')

    def get_challenge_detail_button(self, product_slug, challenge_id):
        href_value = f"/{product_slug}/challenge/{challenge_id}"
        return self.page.locator(f'a[href="{href_value}"].relative')

    def get_bounty_claim_button(self, bounty_id):
        href_value = f"/bounty-claim/{bounty_id}/"
        return self.page.locator(f'button[hx-post="{href_value}"]')

    def get_actions_dropdown(self, bounty_id):
        return self.page.locator(f"#dropdownHoverButton_{bounty_id}")

    def get_cancel_request_button(self, bounty_claim_id):
        return self.page.locator(f'a[hx-post="/bounty_claim/delete/{bounty_claim_id}"]')
