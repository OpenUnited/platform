import os

from django.utils import timezone

import pytest
from model_bakery import baker
from playwright.sync_api import sync_playwright


@pytest.fixture(scope="module")
def playwright_context():
    os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
    playwright = sync_playwright().start()
    yield playwright
    playwright.stop()


@pytest.fixture
def browser_context(playwright_context):
    # browser = playwright_context.chromium.launch(headless=False,slow_mo=300)
    browser = playwright_context.chromium.launch()
    yield browser
    browser.close()


@pytest.fixture
def page_context(browser_context):
    page = browser_context.new_page()
    yield page


@pytest.fixture
def create_user(db):
    username = "testuser"
    password = "12345"
    first_name = "Test"
    last_name = "User"
    full_name = f"{first_name} {last_name}"

    user = baker.make(
        "security.User",
        username=username,
        password=password,
        first_name=first_name,
        last_name=last_name,
    )
    user.set_password(password)
    user.save()
    person = baker.make("talent.Person", user=user, photo="image.png", full_name=full_name)

    return user, username, password, person


@pytest.fixture
def setup_bounty(db, create_user):
    user, username, password, person = create_user

    now = timezone.now()
    product = baker.make(
        "product_management.Product",
        name="PetConnect",
        slug="petconnect",
        created_at=now,
        updated_at=now,
    )
    product_tree = baker.make("product_management.ProductTree", product=product, name="PetConnect Tree")
    product_area = baker.make("product_management.ProductArea", product_tree=product_tree, name="PetConnect Area")
    initiative = baker.make("product_management.Initiative", product=product, name="PetConnect Service Integration")
    challenge = baker.make(
        "product_management.Challenge",
        product_area=product_area,
        initiative=initiative,
        product=product,
        status="Active",
        title="Pet Emergency Alert System",
        short_description="Introduce pet grooming scheduler feature.",
        priority="High",
        created_by=person,
    )
    bounty = baker.make(
        "product_management.Bounty",
        challenge=challenge,
        title="Pet Sitting Made Easy",
        status="Available",
        description="Information Systems & Networking (Python)",
    )
    return product, challenge, bounty, person, username, password
