import pytest
from pytest_mock import MockerFixture
from django.utils import timezone
import datetime

from apps.capabilities.product_management.services import ProductManagementService
from apps.engagement.models import (
    NotifiableEvent,
    AppNotification,
    EmailNotification,
    NotificationPreference
)
from apps.capabilities.talent.models import Person
from apps.capabilities.commerce.models import Organisation

@pytest.fixture
def person():
    return Person.objects.create(name="Test Person")

@pytest.fixture
def org():
    return Organisation.objects.create(name="Test Org")

@pytest.fixture
def notification_preferences(person):
    return NotificationPreference.objects.create(
        person=person,
        product_notifications=NotificationPreference.Type.BOTH
    )

@pytest.mark.django_db
class TestNotificationFlow:
    def test_product_created_event_emission(self, mocker: MockerFixture, person):
        """Test that creating a product emits the correct event"""
        mock_event_bus = mocker.patch('apps.event_hub.services.django_q_event_bus.DjangoQEventBus.publish')
        
        product = ProductManagementService.create_product(
            {"name": "Test Product"},
            person=person
        )

        mock_event_bus.assert_called_once_with(
            'product.created',
            {
                'organisation_id': None,
                'person_id': person.id,
                'name': "Test Product",
                'url': product.get_absolute_url()
            }
        )

    def test_handle_product_created_org_product(self, org, notification_preferences):
        """Test handling product.created event for org product"""
        from apps.engagement.events import handle_product_created
        
        payload = {
            'organisation_id': org.id,
            'name': "Test Product",
            'url': "/products/test"
        }
        
        handle_product_created(payload)
        
        # Verify NotifiableEvent was created
        event = NotifiableEvent.objects.first()
        assert event is not None
        assert event.event_type == NotifiableEvent.EventType.PRODUCT_CREATED
        
        # Verify notifications were created
        app_notif = AppNotification.objects.first()
        email_notif = EmailNotification.objects.first()
        assert app_notif is not None
        assert email_notif is not None

    def test_handle_product_created_personal_product(self, person, notification_preferences):
        """Test handling product.created event for personal product"""
        from apps.engagement.events import handle_product_created
        
        payload = {
            'person_id': person.id,
            'name': "Test Product",
            'url': "/products/test"
        }
        
        handle_product_created(payload)
        
        # Verify notifications for personal product
        event = NotifiableEvent.objects.first()
        assert event.person == person

    def test_notification_preference_respected(self, person):
        """Test that notifications respect user preferences"""
        # Set preference to apps only
        prefs = NotificationPreference.objects.create(
            person=person,
            product_notifications=NotificationPreference.Type.APPS
        )
        
        from apps.engagement.events import handle_product_created
        handle_product_created({
            'person_id': person.id,
            'name': "Test Product",
            'url': "/test"
        })
        
        # Should have app notification but not email
        assert AppNotification.objects.exists()
        assert not EmailNotification.objects.exists()

    def test_notification_cleanup(self, person):
        """Test that old notifications are cleaned up"""
        # Create expired notification
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

    def test_notification_template_rendering(self, person, notification_preferences):
        """Test that notification templates render correctly"""
        from apps.engagement.models import AppNotificationTemplate
        
        # Create template
        template = AppNotificationTemplate.objects.create(
            event_type=NotifiableEvent.EventType.PRODUCT_CREATED,
            title_template="New Product: {name}",
            message_template="Product {name} was created. View it here: {url}",
            permitted_params="name,url"
        )
