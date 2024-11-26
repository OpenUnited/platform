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
        title="New Product: {name}",
        template="A new product {name} has been created. View it at {url}",
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
@pytest.mark.django_db
def cleanup_test_data():
    """Clean up notifications after each test"""
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

@pytest.fixture
def product_manager(db):
    """Create a product manager user"""
    user = get_user_model().objects.create_user(
        username="productmanager",
        email="pm@example.com",
        password="testpass123"
    )
    return Person.objects.create(
        user=user,
        full_name="Product Manager",
        preferred_name="PM"
    )

@pytest.fixture
def org_manager(db):
    """Create an organization manager user"""
    user = get_user_model().objects.create_user(
        username="orgmanager",
        email="om@example.com",
        password="testpass123"
    )
    return Person.objects.create(
        user=user,
        full_name="Org Manager",
        preferred_name="OM"
    )

@pytest.mark.django_db
class TestNotificationCreation:
    """Tests for notification creation and content generation.
    
    These tests verify:
    - Notification creation based on user preferences
    - Template rendering and content formatting
    - Error handling for invalid/missing templates
    """

    @pytest.fixture(autouse=True)
    def setup_event_bus(self):
        """Register event handlers with event bus"""
        from apps.event_hub.services.event_bus import EventBus
        from apps.engagement.events import handle_product_created
        
        event_bus = EventBus()
        event_bus.register_listener(EventTypes.PRODUCT_CREATED, handle_product_created)
        return event_bus

    @pytest.fixture
    def event_data(self, org, person):
        """Standard event data for testing"""
        return {
            'organisationId': org.id,
            'name': "Test Product",
            'url': "/products/test-product/",
            'productId': 1,
            'personId': person.id
        }

    @pytest.fixture(autouse=True)
    def configure_sync_mode(self, settings):
        """Configure Django-Q for synchronous execution"""
        settings.DJANGO_Q = {
            'sync': True,
            'timeout': 30,
            'save_limit': 0
        }
        
        # Configure event bus for sync mode
        settings.EVENT_BUS = {
            'BACKEND': 'apps.event_hub.services.backends.django_q.DjangoQBackend',
            'TASK_COMPLETE_HOOK': None  # Disable the hook in sync mode
        }

    @pytest.mark.django_db(transaction=True)
    def test_creates_both_notifications_when_preference_is_both(
        self, 
        person, 
        event_data, 
        notification_preferences, 
        app_template, 
        email_template, 
        product,
        transactional_db
    ):
        """
        When user preferences are set to BOTH:
        - Should create both app and email notifications
        - Should format templates correctly
        """
        from apps.event_hub.services.event_bus import get_event_bus
        event_bus = get_event_bus()

        # Commit any pending fixture data
        from django.db import transaction
        transaction.commit()

        # Emit event instead of publish
        event_bus.publish(EventTypes.PRODUCT_CREATED, event_data)

        # Add small delay to allow for task processing
        import time
        time.sleep(0.1)

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

        from apps.event_hub.services.event_bus import EventBus
        event_bus = EventBus()
        event_bus.publish(EventTypes.PRODUCT_CREATED, event_data)

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

        from apps.event_hub.services.event_bus import EventBus
        event_bus = EventBus()
        event_bus.publish(EventTypes.PRODUCT_CREATED, event_data)

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
        app_template.template = "Product: {invalid_param}"
        app_template.save()
        
        from apps.event_hub.services.event_bus import EventBus
        event_bus = EventBus()
        event_bus.publish(EventTypes.PRODUCT_CREATED, event_data)
        
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

        from apps.event_hub.services.event_bus import EventBus
        event_bus = EventBus()
        event_bus.publish(EventTypes.PRODUCT_CREATED, event_data)

        event = NotifiableEvent.objects.get(
            event_type=EventTypes.PRODUCT_CREATED,
            person=person
        )
        
        notification = AppNotification.objects.get(event=event)
        assert notification.message == "There was an error processing this notification."

    def test_notifies_all_relevant_stakeholders_for_org_product(
        self,
        product,
        org_manager,
        product_manager,
        event_data,
        notification_preferences,
        app_template,
        email_template,
        mocker
    ):
        """
        When product is org-owned:
        - Should notify product managers
        - Should notify org managers
        """
        # Mock RoleService methods
        mocker.patch(
            'apps.capabilities.security.services.RoleService.get_product_managers',
            return_value=[product_manager]
        )
        mocker.patch(
            'apps.capabilities.security.services.RoleService.get_organisation_managers',
            return_value=[org_manager]
        )

        from apps.event_hub.services.event_bus import EventBus
        event_bus = EventBus()
        event_bus.publish(EventTypes.PRODUCT_CREATED, event_data)

        # Verify notifications were created for both managers
        assert NotifiableEvent.objects.filter(person=product_manager).exists()
        assert NotifiableEvent.objects.filter(person=org_manager).exists()

    def test_notifies_owner_for_personal_product(
        self,
        person,
        product,
        event_data,
        notification_preferences,
        app_template,
        email_template
    ):
        """
        When product is personally owned:
        - Should notify the product owner
        """
        # Make product personally owned
        product.organisation = None
        product.person = person
        product.visibility = product.Visibility.GLOBAL
        product.save()

        from apps.event_hub.services.event_bus import EventBus
        event_bus = EventBus()
        event_bus.publish(EventTypes.PRODUCT_CREATED, event_data)

        # Verify notification was created for owner
        assert NotifiableEvent.objects.filter(person=person).exists()

    def test_notifications_are_distinct(
        self,
        product,
        person,
        event_data,
        notification_preferences,
        app_template,
        email_template,
        mocker
    ):
        """
        When a person has multiple roles:
        - Should only create one notification
        """
        # Mock person as both product and org manager
        mocker.patch(
            'apps.capabilities.security.services.RoleService.get_product_managers',
            return_value=[person]
        )
        mocker.patch(
            'apps.capabilities.security.services.RoleService.get_organisation_managers',
            return_value=[person]
        )

        from apps.event_hub.services.event_bus import EventBus
        event_bus = EventBus()
        event_bus.publish(EventTypes.PRODUCT_CREATED, event_data)

        # Verify only one notification was created
        assert NotifiableEvent.objects.filter(person=person).count() == 1