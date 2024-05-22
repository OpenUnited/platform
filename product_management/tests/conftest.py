from openunited.tests.conftest import *
from product_management.models import Challenge, Bounty


@pytest.fixture
def product_data(organisation):
    return {
        "name": "Test Product",
        "description": "A test product description",
        "short_description": "A test product description",
        "full_description": "A test product description",
        "organisation": organisation,
    }


@pytest.fixture
def product_area_data():
    return {
        "name": "New Area",
        "parent_id": "None",
        "depth": "0",
    }


@pytest.fixture
def challenge_data(product):
    return {
        "title": "Aliquam viverra",
        "description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
        "short_description": "Fusce sed arcu vitae",
        "product": product.pk,
        "reward_type": 1,
        "status": Challenge.ChallengeStatus.ACTIVE,
        "priority": 1,
    }


@pytest.fixture
def challenge_update_data():
    return {
        "title": "Aliquam viverra",
        "description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
        "short_description": "Fusce sed arcu vitae",
        "reward_type": 1,
        "status": Challenge.ChallengeStatus.ACTIVE,
        "priority": 1,
    }


@pytest.fixture
def initiative_data(product):
    return {
        "name": "New Initiative",
        "description": "A new initiative",
        "status": Initiative.InitiativeStatus.ACTIVE,
        "product": product.pk,
    }


@pytest.fixture
def bounty_data(challenge, skill, expertise_list):
    return {
        "title": "Suspendisse dapibus porttitor laoreet.",
        "description": " Fusce laoreet lectus in nisl efficitur fermentum. ",
        "status": Bounty.BountyStatus.AVAILABLE,
        "challenge": challenge.pk,
        "points": 10,
    }
