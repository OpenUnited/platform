from apps.common.forms import AttachmentFormSet
from apps.common.tests.conftest import *
from apps.capabilities.product_management.models import Bounty, Challenge, FileAttachment
from django.contrib.auth import get_user_model
from apps.capabilities.talent.models import Person
from apps.capabilities.commerce.models import Organisation
from apps.capabilities.security.models import User
import uuid


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """Configure DB for testing"""
    pass


def pytest_configure():
    """Configure pytest settings"""
    from django.conf import settings
    
    settings.MIGRATION_MODULES = {
        'auth': None,
        'contenttypes': None,
        'default': None,
        'sessions': None,
        'core': None,
        'profiles': None,
        'product_management': None,
        'talent': None,
        'security': None,
        # add other apps as needed
    }


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
def product_area_data(product_area):
    return {
        "name": "New Area",
        "depth": "0",
        "parent_id": product_area.pk,
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


@pytest.fixture
def user():
    """Returns a test user"""
    return User.objects.create(
        username=f"testuser_{uuid.uuid4().hex[:8]}",
        email="test@example.com",
        is_active=True
    )


@pytest.fixture
def person(user):
    """Returns the person associated with the test user"""
    from apps.capabilities.talent.models import Person
    try:
        return user.person
    except User.person.RelatedObjectDoesNotExist:
        return Person.objects.create(
            user=user,
            full_name=user.username,
            preferred_name=user.username
        )


@pytest.fixture
def product_with_person(person):
    """Create a test product owned by a person"""
    from apps.capabilities.product_management.models import Product
    
    return Product.objects.create(
        name="Test Product",
        slug="test-product",
        person=person,
        visibility='GLOBAL'
    )


@pytest.fixture
def product_with_org(organisation):
    """Create a test product owned by an organization"""
    from apps.capabilities.product_management.models import Product
    
    return Product.objects.create(
        name="Org Product",
        slug="org-product",
        organisation=organisation,
        visibility='GLOBAL'
    )


@pytest.fixture
def authenticated_client(client, user):
    """Returns an authenticated client"""
    client.force_login(user)
    return client


@pytest.fixture
def product(person):
    """Create a test product owned by the test person"""
    from apps.capabilities.product_management.models import Product
    
    return Product.objects.create(
        name='Test Product',
        short_description='A test product',
        visibility='GLOBAL',
        person=person
    )
