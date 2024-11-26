import pytest
import time
from threading import Event
from django.test import override_settings
from django.core.cache import cache
from django_q.cluster import Cluster
from django_q.models import OrmQ, Task
from django_q.brokers import get_broker
from django_q.tasks import async_task
from django.db import transaction

from apps.engagement.models import (
    NotifiableEvent,
    AppNotification,
    EmailNotification,
    NotificationPreference,
    AppNotificationTemplate,
    EmailNotificationTemplate
)
from apps.capabilities.security.models import User
from apps.capabilities.talent.models import Person
from apps.capabilities.product_management.models import Product
from apps.capabilities.commerce.models import Organisation
from apps.event_hub.events import EventTypes
from apps.event_hub.models import EventLog
from apps.event_hub.services.factory import get_event_bus

# Add at the top of the file, after imports
executed_listeners = []

def clear_executed():
    executed_listeners.clear()

class TestNotificationProcessing:
    """Tests for notification processing through the event system.
    
    These tests verify:
    - Event handling and task execution
    - Event bus publication and subscription
    - Multiple listener execution
    - Transaction handling in event context
    """

    @pytest.fixture
    def user(self, db):
        """Create test user"""
        return User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

    @pytest.fixture
    def person(self, user):
        """Create test person with required fields"""
        return Person.objects.create(
            user=user,
            full_name="Test Person",
            preferred_name="Test",
            headline="Test Headline"
        )

    @pytest.fixture
    def organisation(self, db):
        """Create test organisation"""
        return Organisation.objects.create(
            username="testorg",
            name="Test Organisation"
        )

    @pytest.fixture
    def product(self, organisation):
        """Create test product owned by organisation"""
        return Product.objects.create(
            name="Test Product",
            slug="test-product",
            short_description="Test Description",
            organisation=organisation,
            visibility=Product.Visibility.GLOBAL
        )

    @pytest.fixture
    def notification_preferences(self, person):
        """Create notification preferences for test person"""
        return NotificationPreference.objects.create(
            person=person,
            product_notifications=NotificationPreference.Type.BOTH
        )

    @pytest.fixture
    def notification_templates(self, db):
        """Create test notification templates"""
        app_template = AppNotificationTemplate.objects.create(
            event_type=EventTypes.PRODUCT_CREATED,
            title="New Product: {name}",
            template="Product {name} was created at {url}"
        )
        
        email_template = EmailNotificationTemplate.objects.create(
            event_type=EventTypes.PRODUCT_CREATED,
            title="New Product: {name}",
            template="Product {name} was created at {url}"
        )
        
        return app_template, email_template

    @pytest.fixture(scope="class")
    def db_class(self, request):
        """Class-scoped db fixture"""
        marker = request.node.get_closest_marker('django_db')
        django_db_blocker = request.getfixturevalue('django_db_blocker')
        with django_db_blocker.unblock():
            yield

    @pytest.fixture(scope="class")
    def global_broker(self, db_class):
        """Create a single broker instance for all tests"""
        broker = get_broker()
        broker.purge_queue()
        cache.clear()
        return broker

    @pytest.fixture(autouse=True)
    def register_event_listeners(self):
        """Register event listeners for product events"""
        from apps.event_hub.services.factory import get_event_bus
        from apps.engagement.events import handle_product_created
        from django.conf import settings
        
        # Configure Django-Q for sync mode during tests
        settings.DJANGO_Q = {
            'sync': True,  # This makes Django-Q run synchronously
            'timeout': 30,
            'save_limit': 0,
            'orm': 'default'
        }
        
        event_bus = get_event_bus()
        event_bus.register_listener(EventTypes.PRODUCT_CREATED, handle_product_created)
        
        return event_bus

    @pytest.fixture
    def event_data(self, product, person):
        """Standard event data for testing"""
        return {
            'productId': str(product.id),
            'name': product.name,
            'url': f'/products/{product.slug}/',
            'organisationId': str(product.organisation.id),
            'personId': str(person.id)
        }

    @pytest.fixture(autouse=True)
    def configure_sync_mode(self, settings):
        """Configure Django-Q for synchronous execution"""
        settings.DJANGO_Q = {
            'sync': True,
            'timeout': 30,
            'save_limit': 0
        }
        
        # Also need to patch the task_complete hook since it won't be called in sync mode
        settings.EVENT_BUS = {
            'BACKEND': 'apps.event_hub.services.backends.django_q.DjangoQBackend',
            'TASK_COMPLETE_HOOK': None  # Disable the hook in sync mode
        }
        yield

    @pytest.fixture
    def product_manager(self, db):
        """Create a product manager user"""
        user = User.objects.create_user(
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
    def org_manager(self, db):
        """Create an organization manager user"""
        user = User.objects.create_user(
            username="orgmanager",
            email="om@example.com",
            password="testpass123"
        )
        return Person.objects.create(
            user=user,
            full_name="Org Manager",
            preferred_name="OM"
        )

    @pytest.fixture
    def all_notification_preferences(self, product_manager, org_manager):
        """Create notification preferences for all stakeholders"""
        prefs = []
        for person in [product_manager, org_manager]:
            prefs.append(NotificationPreference.objects.create(
                person=person,
                product_notifications=NotificationPreference.Type.BOTH
            ))
        return prefs

    @pytest.mark.django_db(transaction=True)
    def test_async_notification_processing(
        self, transactional_db, person, event_data, notification_preferences,
        notification_templates
    ):
        """Test that notifications are created when events are published."""
        event_bus = get_event_bus()

        # Commit any pending fixture data
        transaction.commit()

        # Add debug logging
        print(f"\nEvent data: {event_data}")
        print(f"Person: {person}")
        print(f"Templates: {notification_templates}")
        print(f"Preferences: {notification_preferences}")

        event_bus.publish(EventTypes.PRODUCT_CREATED, event_data)

        # Add debug for notifications
        events = NotifiableEvent.objects.filter(person=person)
        print(f"Events created: {events.count()}")
        
        notifications = AppNotification.objects.all()
        print(f"All notifications: {notifications.count()}")

        # Since tasks are synchronous, they run immediately
        # Verify that notifications were created
        assert AppNotification.objects.filter(event__person=person).exists(), "App notification not created"
        assert EmailNotification.objects.filter(event__person=person).exists(), "Email notification not created"

    @pytest.mark.django_db(transaction=True)
    def test_event_bus_notification_processing(
        self, person, event_data, notification_preferences,
        notification_templates
    ):
        """Test that notifications are created when events are published."""
        event_bus = get_event_bus()

        # Emit event
        event_bus.publish(EventTypes.PRODUCT_CREATED, event_data)

        # Verify that notifications were created
        assert AppNotification.objects.filter(event__person=person).exists(), "App notification not created"
        assert EmailNotification.objects.filter(event__person=person).exists(), "Email notification not created"

    @pytest.mark.django_db(transaction=True)
    def test_async_multiple_listeners(
        self, person, event_data, notification_preferences, notification_templates
    ):
        """Test that multiple listeners are executed"""
        event_bus = get_event_bus()

        # Reset executed listeners list
        clear_executed()

        # Define the listeners directly in the test
        def listener_1(payload):
            executed_listeners.append('listener_1')
            return True

        def listener_2(payload):
            executed_listeners.append('listener_2')
            return True

        # Register listeners as callable functions instead of strings
        event_bus.register_listener(EventTypes.TEST_MULTIPLE_LISTENERS, listener_1)
        event_bus.register_listener(EventTypes.TEST_MULTIPLE_LISTENERS, listener_2)

        # Debug internal state
        print(f"\nInternal listeners state: {event_bus._listeners}")
        print(f"Publishing event: {EventTypes.TEST_MULTIPLE_LISTENERS}")
        print(f"Event data: {event_data}")

        # Emit event
        event_bus.publish(EventTypes.TEST_MULTIPLE_LISTENERS, event_data)

        # Add small delay to allow for processing
        time.sleep(0.1)

        # Debug output
        print(f"Executed listeners: {executed_listeners}")
        assert len(executed_listeners) == 2, f"Expected 2 listeners to execute, but got {len(executed_listeners)}"

    @pytest.mark.django_db(transaction=True)
    def test_sync_execution_assumptions(self):
        """Test our assumptions about sync execution"""
        event_bus = get_event_bus()
        
        # Track execution
        executed = []
        
        def test_listener(payload):
            executed.append(payload)
            return True

        # Register both callable and string-based listeners
        event_bus.register_listener(EventTypes.TEST_EVENT, test_listener)
        event_bus.register_listener(EventTypes.TEST_EVENT, 'apps.engagement.tests.test_listeners.listener_1')
        
        # Emit event
        test_payload = {'test': 'data'}
        event_bus.publish(EventTypes.TEST_EVENT, test_payload)
        
        # Verify assumptions
        assert len(executed) == 1, "Callable listener should execute immediately"
        assert EventLog.objects.filter(payload=test_payload, processed=True).exists(), "Event log should be marked as processed"

    @pytest.mark.django_db(transaction=True)
    def test_async_notification_processing_for_org_product(
        self, 
        transactional_db, 
        product_manager, 
        org_manager,
        event_data, 
        all_notification_preferences,
        notification_templates,
        mocker
    ):
        """Test that notifications are created for all stakeholders when events are published."""
        event_bus = get_event_bus()

        # Mock RoleService methods
        mocker.patch(
            'apps.capabilities.security.services.RoleService.get_product_managers',
            return_value=[product_manager]
        )
        mocker.patch(
            'apps.capabilities.security.services.RoleService.get_organisation_managers',
            return_value=[org_manager]
        )

        # Commit any pending fixture data
        transaction.commit()

        # Emit event
        event_bus.publish(EventTypes.PRODUCT_CREATED, event_data)

        # Verify notifications for product manager
        assert NotifiableEvent.objects.filter(person=product_manager).exists()
        assert AppNotification.objects.filter(event__person=product_manager).exists()
        assert EmailNotification.objects.filter(event__person=product_manager).exists()

        # Verify notifications for org manager
        assert NotifiableEvent.objects.filter(person=org_manager).exists()
        assert AppNotification.objects.filter(event__person=org_manager).exists()
        assert EmailNotification.objects.filter(event__person=org_manager).exists()

    @pytest.mark.django_db(transaction=True)
    def test_async_notification_processing_for_personal_product(
        self,
        transactional_db,
        person,
        product,
        event_data,
        notification_preferences,
        notification_templates
    ):
        """Test that notifications are created for personal product owner."""
        event_bus = get_event_bus()

        # Make product personally owned
        product.organisation = None
        product.person = person
        product.save()

        # Commit any pending fixture data
        transaction.commit()

        # Emit event
        event_bus.publish(EventTypes.PRODUCT_CREATED, event_data)

        # Verify notifications for owner
        assert NotifiableEvent.objects.filter(person=person).exists()
        assert AppNotification.objects.filter(event__person=person).exists()
        assert EmailNotification.objects.filter(event__person=person).exists()

    @pytest.mark.django_db(transaction=True)
    def test_async_notification_processing_distinct(
        self,
        transactional_db,
        person,
        event_data,
        notification_preferences,
        notification_templates,
        mocker
    ):
        """Test that notifications are distinct when person has multiple roles."""
        event_bus = get_event_bus()

        # Mock person as both product and org manager
        mocker.patch(
            'apps.capabilities.security.services.RoleService.get_product_managers',
            return_value=[person]
        )
        mocker.patch(
            'apps.capabilities.security.services.RoleService.get_organisation_managers',
            return_value=[person]
        )

        # Commit any pending fixture data
        transaction.commit()

        # Emit event
        event_bus.publish(EventTypes.PRODUCT_CREATED, event_data)

        # Verify only one set of notifications was created
        assert NotifiableEvent.objects.filter(person=person).count() == 1
        assert AppNotification.objects.filter(event__person=person).count() == 1
        assert EmailNotification.objects.filter(event__person=person).count() == 1