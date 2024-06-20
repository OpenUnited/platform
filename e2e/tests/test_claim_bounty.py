from datetime import datetime, timedelta

from apps.talent.models import BountyClaim
from e2e.helpers import login_user
from e2e.pages.challenge_details_page import ChallengeDetailPage


def test_claim_bounty(live_server, page_context, setup_bounty):
    product, challenge, bounty, _, username, password = setup_bounty
    login_user(page_context, live_server.url, username, password)

    page = ChallengeDetailPage(page_context)
    page_context.wait_for_timeout(1500)
    assert BountyClaim.objects.filter(bounty=bounty.id).count() == 0

    page_context.reload()
    page_context.wait_for_timeout(5000)
    challenge_detail_button = page.get_challenge_detail_button(product.slug, challenge.id)

    challenge_detail_button.click()
    page_context.wait_for_timeout(1500)

    bounty_claim_button = page.get_bounty_claim_button(bounty.id)
    bounty_claim_button.click()

    page_context.wait_for_timeout(500)
    page.bounty_add_btn.click()
    page_context.wait_for_timeout(500)

    future_date = datetime.now() + timedelta(days=10)
    page_context.wait_for_timeout(500)

    day = future_date.strftime("%d")
    month = future_date.strftime("%m")
    year = future_date.strftime("%Y")

    # Clear the date input fields before typing
    page.expected_submission_date.fill(f"{year}-{month}-{day}")

    page.terms_check_box.check()

    page.request_claim_button.click()

    page_context.wait_for_timeout(1500)

    bounty_claim = BountyClaim.objects.get(bounty=bounty.id)
    assert bounty_claim.status == BountyClaim.Status.REQUESTED
