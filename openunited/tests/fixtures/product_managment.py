import pytest, random
from model_bakery import baker
from product_management.models import Product
from django.apps import apps


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    print("Enable database access for all tests")


@pytest.fixture
def products(random_string):
    _products = baker.make(
        "product_management.Product",
        name=baker.seq(random_string),
        is_private=False,
        _quantity=20,
    )
    for product in _products[:10]:
        product.is_private = True
        product.save()

    return _products


@pytest.fixture
def product(random_string):
    return baker.make(
        "product_management.Product",
        name=random_string,
    )


@pytest.fixture
def owned_products(user, content_type, random_string):
    _products = baker.make(
        "product_management.Product",
        content_type=content_type,
        object_id=content_type.pk,
        name=baker.seq(random_string),
        is_private=False,
        _quantity=10,
    )

    for product in _products[:10]:
        product.is_private = True
        product.save()


@pytest.fixture
def owned_product(user, content_type, random_string):
    return baker.make(
        "product_management.Product",
        content_type=content_type,
        object_id=content_type.pk,
        name=random_string,
    )


@pytest.fixture
def productAreas():
    return baker.make("product_management.ProductArea", _quantity=10)


@pytest.fixture
def productArea():
    return baker.make("product_management.ProductArea")


@pytest.fixture
def challenges(owned_product, user):
    return baker.make(
        "product_management.Challenge",
        product=owned_product,
        created_by=user.person,
        _quantity=10,
    )


@pytest.fixture
def challenge(owned_product, user):
    return baker.make(
        "product_management.Challenge",
        product=owned_product,
        created_by=user.person,
    )


@pytest.fixture
def product_initiatives(owned_product):
    return baker.make(
        "product_management.Initiative",
        product=owned_product,
        _quantity=10,
    )


@pytest.fixture
def product_initiatives(owned_product):
    return baker.make(
        "product_management.Initiative",
        product=owned_product,
    )


@pytest.fixture
def bounties(challenge, skill):
    return baker.make(
        "product_management.Bounty",
        skill=skill,
        challenge=challenge,
        _quantity=100,
    )


@pytest.fixture
def bounty(challenge, skill):
    return baker.make(
        "product_management.Bounty", skill=skill, challenge=challenge
    )


@pytest.fixture
def product_ideas(owned_product, user):
    return baker.make(
        "product_management.Idea",
        product=owned_product,
        person=user.product,
        _quantity=10,
    )


@pytest.fixture
def product_idea(owned_product, user):
    return baker.make(
        "product_management.Idea",
        product=owned_product,
        person=user.product,
    )


@pytest.fixture
def product_bug(owned_product, user):
    return baker.make(
        "product_management.Idea",
        product=owned_product,
        person=user.product,
        _quantity=10,
    )


@pytest.fixture
def product_bug(owned_product, user):
    return baker.make(
        "product_management.Idea",
        product=owned_product,
        person=user.product,
    )


@pytest.fixture(autouse=True)
def video_link():
    return "https://www.youtube.com/embed/HlgG395PQWw"
