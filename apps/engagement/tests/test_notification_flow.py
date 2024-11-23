import pytest
from pytest_mock import MockerFixture
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.capabilities.product_management.services import ProductManagementService
from apps.engagement.models import (
    NotifiableEvent,
    AppNotification,
    EmailNotification,
    NotificationPreference,
    AppNotificationTemplate,
    EmailNotificationTemplate
)
from apps.capabilities.talent.models import Person
from apps.capabilities.commerce.models import Organisation, Product
from apps.event_hub.events import EventTypes

@pytest.fixture
def user():
    User = get_user_model()
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123"
    )

@pytest.fixture
def person(user):
    return Person.objects.create(
        user=user,
        full_name="Test Person",
        preferred_name="Test",
        headline="Test Headline",
        overview="Test Overview"
    )

@pytest.fixture
def org():
    return Organisation.objects.create(
        name="Test Org"
    )

@pytest.fixture
def notification_preferences(person):
    return NotificationPreference.objects.create(
        person=person,
        product_notifications=NotificationPreference.Type.BOTH
    )

@pytest.fixture
def app_template():
    return AppNotificationTemplate.objects.create(
        event_type=EventTypes.PRODUCT_CREATED,
        title_template="New Product: {name}",
        message_template="A new product {name} has been created. View it at {url}",
        permitted_params="name,url"
    )

@pytest.fixture
def email_template():
    return EmailNotificationTemplate.objects.create(
        event_type=EventTypes.PRODUCT_CREATED,
        title="New Product: {name}",
        template="A new product {name} has been created. View it at {url}",
        permitted_params="name,url"
    )

@pytest.fixture(autouse=True)
def cleanup_test_data():
    yield
    NotifiableEvent.objects.all().delete()
    AppNotification.objects.all().delete()
    EmailNotification.objects.all().delete()
    Product.objects.all().delete()

@pytest.fixture
def organisation(db):
    """Create a test organisation"""
    return Organisation.objects.create(
        name="Test Organisation",
        username="testorg"
    )

@pytest.fixture
def product(db, organisation):
    """Create a test product"""
    return Product.objects.create(
        id=1,
        name="Test Product",
        slug="test-product",
        organisation=organisation,  # Required owner
        visibility=Product.Visibility.ORG_ONLY,  # Default visibility for org-owned products
        short_description="A test product"  # Optional but good for completeness
    )

class TestNotificationFlow:
    """Tests for the notification creation flow"""

    @pytest.fixture
    def event_data(self, org, person):
        """Standard event data for testing"""
        return {
            'organisation_id': org.id,
            'name': "Test Product",
            'url': "/products/test-product/",
            'product_id': 1,
            'person_id': person.id
        }

    def test_creates_both_notifications_when_preference_is_both(
        self, 
        person, 
        event_data, 
        notification_preferences, 
        app_template, 
        email_template, 
        product
    ):
        """
        When user preferences are set to BOTH:
        - Should create both app and email notifications
        - Should format templates correctly
        """
        from apps.engagement.events import handle_product_created
        handle_product_created(event_data)

        event = NotifiableEvent.objects.get(
            event_type=EventTypes.PRODUCT_CREATED,
            person=person
        )
        
        # Verify app notification
        app_notification = AppNotification.objects.get(event=event)
        assert app_notification.title == "New Product: Test Product"
        assert app_notification.message == "A new product Test Product has been created. View it at /products/test-product/"

        # Verify email notification
        email_notification = EmailNotification.objects.get(event=event)
        assert email_notification.title == "New Product: Test Product"
        assert email_notification.body == "A new product Test Product has been created. View it at /products/test-product/"

    def test_creates_only_app_notification_when_preference_is_apps(
        self, 
        person, 
        event_data, 
        notification_preferences, 
        app_template, 
        email_template, 
        product
    ):
        """
        When user preferences are set to APPS:
        - Should create only app notification
        - Should not create email notification
        """
        notification_preferences.product_notifications = NotificationPreference.Type.APPS
        notification_preferences.save()

        from apps.engagement.events import handle_product_created
        handle_product_created(event_data)

        event = NotifiableEvent.objects.get(
            event_type=EventTypes.PRODUCT_CREATED,
            person=person
        )
        
        assert AppNotification.objects.filter(event=event).exists()
        assert not EmailNotification.objects.filter(event=event).exists()

    def test_creates_only_email_notification_when_preference_is_email(
        self,
        person,
        event_data,
        notification_preferences,
        app_template,
        email_template,
        product
    ):
        """
        When user preferences are set to EMAIL:
        - Should create only email notification
        - Should not create app notification
        """
        notification_preferences.product_notifications = NotificationPreference.Type.EMAIL
        notification_preferences.save()

        from apps.engagement.events import handle_product_created
        handle_product_created(event_data)

        event = NotifiableEvent.objects.get(
            event_type=EventTypes.PRODUCT_CREATED,
            person=person
        )
        
        assert EmailNotification.objects.filter(event=event).exists()
        assert not AppNotification.objects.filter(event=event).exists()

    def test_handles_invalid_template_gracefully(
        self, 
        person, 
        event_data, 
        notification_preferences, 
        app_template, 
        email_template, 
        product
    ):
        """
        When template contains invalid parameters:
        - Should create notification with error message
        - Should not raise exception
        """
        app_template.message_template = "Product: {invalid_param}"
        app_template.save()
        
        from apps.engagement.events import handle_product_created
        handle_product_created(event_data)
        
        notification = AppNotification.objects.get(
            event__event_type=EventTypes.PRODUCT_CREATED,
            event__person=person
        )
        assert notification.message == "There was an error processing this notification."

    def test_handles_missing_template_gracefully(
        self,
        person,
        event_data,
        notification_preferences,
        product
    ):
        """
        When templates don't exist:
        - Should create notification with error message
        - Should not raise exception
        """
        # Delete any existing templates
        AppNotificationTemplate.objects.all().delete()
        EmailNotificationTemplate.objects.all().delete()

        from apps.engagement.events import handle_product_created
        handle_product_created(event_data)

        event = NotifiableEvent.objects.get(
            event_type=EventTypes.PRODUCT_CREATED,
            person=person
        )
        
        notification = AppNotification.objects.get(event=event)
        assert notification.message == "There was an error processing this notification."