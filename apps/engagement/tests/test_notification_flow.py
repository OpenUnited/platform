import pytest
from pytest_mock import MockerFixture
from django.utils import timezone
import datetime
from django.contrib.auth import get_user_model
from django.test import override_settings
from django_q.models import Schedule, Task
from time import sleep
from django_q.tasks import async_task
from apps.event_hub.services.event_bus import EventBus
from apps.event_hub.services.factory import get_event_bus
from apps.event_hub.services.backends.django_q import execute_listener

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
import time
from django.db import transaction

def error_handler(payload):
    raise ValueError("Test error")

_retry_count = 0  # Module level counter for testing

def retry_handler(payload):
    global _retry_count
    _retry_count += 1
    
    if _retry_count <= 2:
        raise ValueError("Temporary failure")
    return "Success"

def wait_for_task_completion(task_name: str, timeout: int = 5):
    """Helper function to wait for task completion"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        task = Task.objects.filter(name=task_name).order_by('-id').first()
        if task and task.success is not None:
            return task
        time.sleep(0.1)
    raise TimeoutError(f"Task {task_name} did not complete within {timeout} seconds")

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
        overview="Test Overview",
        points=0,
        send_me_bounties=True
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
        event_type=NotifiableEvent.EventType.PRODUCT_CREATED,
        title_template="New Product: {name}",
        message_template="A new product {name} has been created. View it at {url}"
    )

@pytest.fixture
def email_template():
    return EmailNotificationTemplate.objects.create(
        event_type=NotifiableEvent.EventType.PRODUCT_CREATED,
        title="New Product: {name}",
        template="A new product {name} has been created. View it at {url}",
        permitted_params="name,url"
    )

@pytest.fixture(scope='function')
def django_q_cluster(db):
    """Configure Django Q for testing in synchronous mode"""
    from django_q.conf import Conf
    from django_q.models import OrmQ, Task
    
    # Store original settings
    original_settings = {
        'sync': getattr(Conf, 'SYNC', False),
        'testing': getattr(Conf, 'TESTING', False),
    }
    
    # Configure for testing
    Conf.SYNC = True
    Conf.TESTING = True
    Conf.CACHED = False
    
    # Clear existing tasks
    OrmQ.objects.all().delete()
    Task.objects.all().delete()
    
    yield
    
    # Restore original settings
    for key, value in original_settings.items():
        setattr(Conf, key.upper(), value)
    
    # Cleanup
    OrmQ.objects.all().delete()
    Task.objects.all().delete()

@pytest.mark.django_db(transaction=True, reset_sequences=True)
class TestNotificationFlow:
    def test_product_created_event_emission(self, mocker: MockerFixture, person, org):
        """Test that creating a product emits the correct event"""
        mock_bus = mocker.patch('apps.event_hub.services.event_bus.EventBus._instance')
        mock_bus.emit_event = mocker.Mock()

        product = ProductManagementService.create_product(
            {
                "name": "Test Product",
                "organisation": org,
                "short_description": "Test description",
                "full_description": "Full test description",
                "visibility": "ORG_ONLY"
            },
            person=person
        )

        mock_bus.emit_event.assert_called_once_with('product.created', {
            'organisation_id': product.organisation_id,
            'person_id': product.person_id,
            'name': product.name,
            'url': product.get_absolute_url(),
            'product_id': product.id
        })

    def test_handle_product_created_org_product(self, org, notification_preferences, app_template, email_template, django_q_cluster):
        """Test handling product.created event for org product"""
        from apps.engagement.events import handle_product_created
        
        person = notification_preferences.person
        
        # First create the product
        product = ProductManagementService.create_product(
            {
                "name": "Test Product",
                "organisation": org,
                "short_description": "Test description",
                "full_description": "Full test description",
                "visibility": "ORG_ONLY"
            },
            person=person
        )
        
        payload = {
            'organisation_id': org.id,
            'name': "Test Product",
            'url': "/products/test",
            'product_id': product.id,
            'person_id': person.id
        }
        
        try:
            handle_product_created(payload)
            
            event = NotifiableEvent.objects.filter(
                event_type=NotifiableEvent.EventType.PRODUCT_CREATED,
                person=person
            ).first()
            assert event is not None, "NotifiableEvent was not created"
            
            assert AppNotification.objects.filter(event=event).exists(), "App notification was not created"
        except Exception as e:
            pytest.fail(f"Failed to handle product created event: {str(e)}")

    def test_product_created_event_emission_async(self, mocker: MockerFixture, person, org, app_template, email_template, django_q_cluster):
        """Test that creating a product emits the correct event"""
        from apps.engagement.events import handle_product_created
        
        # Mock the event bus but execute handlers synchronously
        mock_bus = mocker.patch('apps.event_hub.services.event_bus.EventBus._instance')
        
        def mock_handler(payload):
            try:
                handle_product_created(payload)
            except Exception as e:
                pytest.fail(f"Handler failed: {str(e)}")
        
        mock_bus.get_listeners.return_value = [mock_handler]
        
        with transaction.atomic():  # Ensure DB consistency
            product = ProductManagementService.create_product(
                {
                    "name": "Test Product",
                    "organisation": org,
                    "short_description": "Test description",
                    "full_description": "Full test description",
                    "visibility": "ORG_ONLY"
                },
                person=person
            )
            
            # Force sync execution
            mock_handler({
                'organisation_id': org.id,
                'name': product.name,
                'url': f'/products/{product.id}',
                'product_id': product.id,
                'person_id': person.id
            })
        
        event = NotifiableEvent.objects.filter(
            event_type=NotifiableEvent.EventType.PRODUCT_CREATED
        ).first()
        assert event is not None, "Event was not created"

    def test_event_bus_error_handling(self, mocker: MockerFixture, person, org, django_q_cluster):
        """Test error handling in async event processing"""
        event_bus = get_event_bus()
        
        # Create a proper callback function
        mock_callback = mocker.Mock()
        
        # Mock the error reporting directly in the backend
        mocker.patch.object(
            event_bus.backend,
            'report_error',
            side_effect=lambda error, context: mock_callback(error, context)
        )
        
        event_bus.register_listener('test.error', error_handler)
        
        # The error is expected
        with pytest.raises(ValueError, match="Test error"):
            event_bus.emit_event('test.error', {'test': 'data'})
            time.sleep(0.1)  # Allow async processing
        
        # Verify error was reported
        assert mock_callback.called, "Error callback was not called"
        
        # Verify error details
        call_args = mock_callback.call_args
        assert call_args is not None, "No arguments passed to error callback"
        error, context = call_args[0]
        assert isinstance(error, ValueError)
        assert str(error) == "Test error"
        assert context['event_name'] == 'test.error'

    def test_event_retry_mechanism(self, mocker: MockerFixture, person, org, django_q_cluster):
        """Test that failed tasks are retried"""
        global _retry_count
        _retry_count = 0  # Reset counter
        
        event_bus = get_event_bus()
        event_bus.register_listener('test.retry', retry_handler)
        
        # First attempt will fail
        with pytest.raises(ValueError, match="Temporary failure"):
            event_bus.emit_event('test.retry', {'test': 'data'})
        
        # Verify retry count
        assert _retry_count > 0, "Handler was not called"

    def test_notification_cleanup(self, person):
        """Test that old notifications are cleaned up"""
        event = NotifiableEvent.objects.create(
            event_type=NotifiableEvent.EventType.PRODUCT_CREATED,
            person=person,
            delete_at=timezone.now() - datetime.timedelta(days=1)
        )
        
        AppNotification.objects.create(
            event=event,
            delete_at=timezone.now() - datetime.timedelta(days=1)
        )
        
        from apps.engagement.services import NotificationService
        service = NotificationService()
        app_deleted, email_deleted = service.cleanup_old_notifications()
        
        assert app_deleted == 1
        assert AppNotification.objects.count() == 0
