from apps.common.forms import AttachmentFormSet
from apps.common.models import FileAttachment
from apps.openunited.tests.conftest import *
from apps.product_management.models import Bounty, Challenge


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
def attachment_formset():
    return AttachmentFormSet(queryset=FileAttachment.objects.none())


@pytest.fixture
def challenge_data(product, attachment_formset):
    return {
        "title": "Aliquam viverra",
        "description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
        "short_description": "Fusce sed arcu vitae",
        "product": product.pk,
        "status": Challenge.ChallengeStatus.ACTIVE,
        "priority": Challenge.ChallengePriority.HIGH,
        "reward_type": Challenge.RewardType.LIQUID_POINTS,
        "attachment_formset": attachment_formset,
    }


@pytest.fixture
def challenge_update_data(attachment_formset):
    return {
        "title": "Aliquam viverra",
        "description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
        "short_description": "Fusce sed arcu vitae",
        "status": Challenge.ChallengeStatus.ACTIVE,
        "priority": Challenge.ChallengePriority.HIGH,
        "reward_type": Challenge.RewardType.LIQUID_POINTS,
        "attachment_formset": attachment_formset,
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
def bounty_data(challenge, attachment_formset, skill, expertise_list):
    return {
        "title": "Suspendisse dapibus porttitor laoreet.",
        "description": " Fusce laoreet lectus in nisl efficitur fermentum. ",
        "status": Bounty.BountyStatus.AVAILABLE,
        "challenge": challenge.pk,
        "points": 10,
        "attachment_formset": attachment_formset,
    }
