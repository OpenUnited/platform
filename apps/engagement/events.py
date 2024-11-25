from typing import Dict
import logging
from apps.capabilities.security.services import RoleService
from apps.capabilities.commerce.models import Organisation, Product
from apps.engagement.models import (
    NotifiableEvent,
    NotificationPreference,
    AppNotificationTemplate,
    AppNotification,
    EmailNotificationTemplate,
    EmailNotification
)
from apps.capabilities.talent.models import Person
from apps.capabilities.security.models import OrganisationPersonRoleAssignment
from apps.event_hub.events import EventTypes
from apps.event_hub.services.event_bus import EventBus

logger = logging.getLogger(__name__)

def create_notification(event_type: str, person_id: str, message: str) -> NotifiableEvent:
    """Create a simple notification event with error message"""
    event = NotifiableEvent.objects.create(
        event_type=event_type,
        person_id=person_id,
        params={'error_message': message}
    )
    
    AppNotification.objects.create(
        event=event,
        title="Notification",
        message=message
    )
    
    return event

def handle_product_created(event_data):
    """Handle product created event by creating NotifiableEvents for relevant stakeholders"""
    try:
        product_id = event_data.get('product_id')
        if not product_id:
            logger.error("No product_id in event payload")
            return False
            
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            logger.error(f"Product {product_id} not found")
            return False

        # Get all stakeholders to notify
        people_to_notify = set()
        
        if product.organisation:
            people_to_notify.update(RoleService.get_organisation_managers(product.organisation))
            people_to_notify.update(RoleService.get_product_managers(product))
        elif product.person:
            people_to_notify.add(product.person)
            
        if not people_to_notify:
            person_id = event_data.get('person_id')
            if person_id:
                try:
                    person = Person.objects.get(id=person_id)
                    people_to_notify.add(person)
                except Person.DoesNotExist:
                    logger.error(f"Person {person_id} not found")
        
        # Create events for each person
        events = []
        for person in people_to_notify:
            event = NotifiableEvent.objects.create(
                event_type=EventTypes.PRODUCT_CREATED,
                person=person,
                params=event_data
            )
            events.append(event)
            
            EventBus().enqueue_task(
                'apps.engagement.tasks.process_notification',
                {'event_id': event.id},
                EventTypes.PRODUCT_CREATED
            )
            
        return len(events) > 0
        
    except Exception as e:
        logger.error(f"Error in handle_product_created: {e}", exc_info=True)
        raise

def handle_product_updated(event_data):
    """Handle product updated event"""
    logger.info(f"Handling product updated event: {event_data}")
    
    event = NotifiableEvent.objects.create(
        event_type=EventTypes.PRODUCT_UPDATED,
        person_id=event_data['person_id'],
        params=event_data
    )
    logger.info(f"Created event: {event}")
    
    EventBus().enqueue_task(
        'apps.engagement.tasks.process_notification',
        {'event_id': event.id},
        EventTypes.PRODUCT_UPDATED
    )
    
    return event
