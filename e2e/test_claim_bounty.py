from model_bakery import baker
from e2e.base import BaseE2ETest
from e2e.pages.challenge_details_page import ChallengeDetailPage
from apps.talent.models import BountyClaim
from django.utils import timezone
from datetime import datetime, timedelta


class TestClaimBounty(BaseE2ETest):
    def setUp(self):
        super().setUp()
        now = timezone.now()
        self.product = baker.make(
            "product_management.Product",
            name="PetConnect",
            slug="petconnect",
            created_at=now,
            updated_at=now,
        )
        product_tree = baker.make("product_management.ProductTree", product=self.product, name="PetConnect Tree")
        product_area = baker.make("product_management.ProductArea", product_tree=product_tree, name="PetConnect Area")
        initiative = baker.make(
            "product_management.Initiative", product=self.product, name="PetConnect Service Integration"
        )
        self.challenge = baker.make(
            "product_management.Challenge",
            product_area=product_area,
            initiative=initiative,
            product=self.product,
            status="Active",
            title="Pet Emergency Alert System",
            short_description="Introduce pet grooming scheduler feature.",
            priority="High",
            created_by=self.person,
        )
        self.bounty = baker.make(
            "product_management.Bounty",
            challenge=self.challenge,
            title="Pet Sitting Made Easy",
            status="Available",
            description="Information Systems & Networking (Python)",
        )

    def test_claim_bounty(self):

        page = ChallengeDetailPage(self.page)
        self.page.wait_for_timeout(1000)
        self.assertEqual(BountyClaim.objects.filter(bounty=self.bounty.id).count(), 0)

        self.page.reload()
        challenge_detail_button = page.get_challenge_detail_button(self.product.slug, self.challenge.id)
        challenge_detail_button.click()
        self.page.wait_for_timeout(500)

        bounty_claim_button = page.get_bounty_claim_button(self.bounty.id)
        bounty_claim_button.click()

        self.page.wait_for_timeout(500)


        future_date = datetime.today() + timedelta(days=10)
        day = future_date.strftime("%d")
        month = future_date.strftime("%m")
        year = future_date.strftime("%Y")

        page.expected_submission_date.type(day)
        page.expected_submission_date.type(month)
        page.expected_submission_date.type(year)    
        page.terms_check_box.check()

        page.request_claim_button.click()

        
        self.page.wait_for_timeout(1000)
        
        bounty_claim = BountyClaim.objects.get(bounty=self.bounty.id)
        self.assertEqual(bounty_claim.status, BountyClaim.Status.REQUESTED)
