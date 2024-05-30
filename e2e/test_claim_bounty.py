from model_bakery import baker
from PIL import Image as ImageFile
from e2e.base import BaseE2ETest
from e2e.pages.login_page import LoginPage
from termcolor import cprint
from product_management.models import *
from talent.models import BountyClaim

# from datetime import datetime
from django.utils import timezone
import tempfile


class TestClaimBounty(BaseE2ETest):
    def setUp(self):
        super().setUp()
        self.page = self.browser.new_page()
        cprint(f"\n\n{self.page=}", "green")
        import string
        import random

        letters = string.ascii_letters + string.digits + string.punctuation
        self.username = "".join(random.choice(letters) for i in range(10))

        self.user_one = baker.make(
            "security.User",
            username=self.username,
            password="12345",
            first_name="sac",
            last_name="tom",
        )
        self.user_one.set_password("12345")
        self.user_one.save()
        self.person = baker.make("talent.Person", user=self.user_one, photo="tmp_file", full_name="asdsa")
        now = timezone.now()

        product = baker.make(
            "product_management.Product",
            name="sample",
            slug="sample",
            created_at=now,
            updated_at=now,
        )
        self.product = product
        product_tree = baker.make("product_management.ProductTree", product=product, name="sample tree")
        product_area = baker.make("product_management.ProductArea", product_tree=product_tree, name="sample area")
        initiative = baker.make("product_management.Initiative", product=product, name="sample initiative")
        challenge = baker.make(
            "product_management.Challenge",
            product_area=product_area,
            initiative=initiative,
            product=product,
            status="Active",
            title="Sample challenge",
            short_description="123",
            priority="High",
            created_by=self.person,
        )
        self.challenge = challenge
        # # Now create the bounty
        bounty = baker.make(
            "product_management.Bounty",
            challenge=challenge,
            title="first bounty",
            status="Available",
            description="eerter",
        )

        # print(bounty)
        cprint(f"\n\n{bounty=}", "green")

        self.bounty = bounty

        qq = challenge.created_by.get_absolute_url()
        cprint(f"\n\n{qq=}", "green")
        qq = challenge.created_by.get_full_name()
        cprint(f"\n\n{qq=}", "green")

        # # self.product = baker.make("product_management.Product", username=self.username, password="12345")
        # product_content_type = ContentType.objects.get(app_label='product_management',model='product')
        # # self.product = Product.objects.create(content_type=product_content_type,object_id=1)
        # # cprint(f'\n\n{self.product=}',"green")
        # product = baker.make('product_management.Product',content_type=product_content_type,object_id=1,name="sample")
        # initiative = baker.make('product_management.Initiative',product=product)
        # challenge = baker.make('product_management.Challenge',initiative=initiative)
        # baker.make('product_management.Bounty',challenge=challenge)
        # # self.challenge = baker.make('product_management.Challenge',content_type=product_content_type,object_id=1,name="sample")

        # # cprint(f'\n\n{self.product=}',"green")

    def test_login123(self):
        login_page = LoginPage(self.page)
        login_page.navigate(f"{self.live_server_url}{login_page.url}")
        login_page.login(self.username, "12345")

        cprint(f"\n\n{self.product.name=}", "green")

        href_value = f"/{self.product.name}/challenge/{self.challenge.id}"
        cprint(f"\n\n{href_value=}", "green")
        self.page.click(f'a[href="{href_value}"]')

        href_value = f"/bounty-claim/{self.bounty.id}/"

        self.page.click(f'button[hx-post="{href_value}"]')

        # expected_submission_date

        self.page.wait_for_timeout(500)

        self.page.locator("#expected_submission_date").type("12")
        self.page.locator("#expected_submission_date").type("12")
        self.page.locator("#expected_submission_date").type("2025")

        self.page.check("#term_checkbox")

        # term_checkbox

        # ajs-button ajs-ok

        res = BountyClaim.objects.all()
        cprint(f"\n\n{res=}", "green")

        self.page.click(f'button[class="ajs-button ajs-ok"]')

        bounty_claim = BountyClaim.objects.first()
        bounty_claim_id = bounty_claim.id
        bounty_claim_status = bounty_claim.status
        self.assertTrue(bounty_claim.status, BountyClaim.Status.REQUESTED)

        self.page.click(f"#dropdownHoverButton_{self.bounty.id}")

        cprint(f"\n\n{bounty_claim_id=}", "red")

        # href_value = f'/bounty_claim/delete/{bounty_claim_id}/'

        self.page.wait_for_timeout(500)

        # self.page.click(f'a[href="{href_value}"]')
        # self.page.click(f'a[href="{href_value}"]')

        self.page.click(f'a[hx-post="/bounty_claim/delete/{bounty_claim_id}"]')

        cprint(f"\n\n{bounty_claim_status=}", "green")

        from time import sleep

        #
        sleep(5000)
        # self.assertTrue(self.page.is_visible("#navbar-menu-button"))
        # self.assertTrue(self.page.is_visible(f"#dropdownHoverButton_{self.bounty.id}"))
