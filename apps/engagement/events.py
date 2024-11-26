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
from django.db import transaction
from apps.event_hub.services.factory import get_event_bus
from django.urls import reverse

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

def handle_product_created(event_type: str = None, payload: dict = None, **kwargs):
    """Handle product created event by creating NotifiableEvents for relevant stakeholders"""
    try:
        payload = payload or kwargs.get('payload', {})
        logger.debug(f"Received product created event payload: {payload}")
        
        product_id = payload.get('productId')
        if product_id is None:
            logger.error(f"No productId in event payload. Payload: {payload}")
            return False
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            logger.error(f"Product {product_id} not found")
            return False

        # Format the notification parameters
        notification_params = {
            'product_name': product.name,
            'product_url': reverse('portal:product-summary', kwargs={'product_slug': product.slug})
        }

        # Get all stakeholders to notify
        people_to_notify = set()
        
        if product.organisation:
            people_to_notify.update(RoleService.get_organisation_managers(product.organisation))
            people_to_notify.update(RoleService.get_product_managers(product))
        elif product.person:
            people_to_notify.add(product.person)
        
        if not people_to_notify:
            person_id = payload.get('personId')
            if person_id:
                try:
                    person = Person.objects.get(id=person_id)
                    people_to_notify.add(person)
                except Person.DoesNotExist:
                    logger.error(f"Person {person_id} not found")
                    
        events = []
        for person in people_to_notify:
            logger.info(f"Person to notify: {person.full_name}")
            with transaction.atomic():
                notifiable_event = NotifiableEvent.objects.create(
                    event_type=EventTypes.PRODUCT_CREATED,
                    person=person,
                    params=notification_params  # Use the formatted params
                )
                logger.info(f"NotifiableEvent created: {notifiable_event.id}")
                events.append(notifiable_event)

                # Use process_notification task directly
                from apps.engagement.tasks import process_notification
                transaction.on_commit(lambda: process_notification(
                    event_type=EventTypes.PRODUCT_CREATED,
                    payload={'event_id': notifiable_event.id}
                ))
        
        return len(events) > 0
        
    except Exception as e:
        logger.error(f"Error in handle_product_created: {e}", exc_info=True)
        return False

def handle_product_updated(event_type: str = None, payload: dict = None, **kwargs):
    """Handle product updated event by creating NotifiableEvents"""
    try:
        payload = payload or kwargs.get('payload', {})
        logger.debug(f"Received product updated event payload: {payload}")
        
        product_id = payload.get('productId')
        if product_id is None:
            logger.error(f"No productId in event payload. Payload: {payload}")
            return False
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            logger.error(f"Product {product_id} not found")
            return False

        # Format the notification parameters
        notification_params = {
            'product_name': product.name,
            'product_url': reverse('portal:product-summary', kwargs={'product_slug': product.slug})
        }

        # Get all stakeholders to notify
        people_to_notify = set()
        
        if product.organisation:
            people_to_notify.update(RoleService.get_organisation_managers(product.organisation))
            people_to_notify.update(RoleService.get_product_managers(product))
        elif product.person:
            people_to_notify.add(product.person)
        
        if not people_to_notify:
            person_id = payload.get('personId')
            if person_id:
                try:
                    person = Person.objects.get(id=person_id)
                    people_to_notify.add(person)
                except Person.DoesNotExist:
                    logger.error(f"Person {person_id} not found")
                    
        events = []
        for person in people_to_notify:
            logger.info(f"Person to notify: {person.full_name}")
            with transaction.atomic():
                notifiable_event = NotifiableEvent.objects.create(
                    event_type=EventTypes.PRODUCT_UPDATED,
                    person=person,
                    params=notification_params  # Use the formatted params instead of raw payload
                )
                logger.info(f"NotifiableEvent created: {notifiable_event.id}")
                events.append(notifiable_event)

                # Use process_notification task directly
                from apps.engagement.tasks import process_notification
                transaction.on_commit(lambda: process_notification(
                    event_type=EventTypes.PRODUCT_UPDATED,
                    payload={'event_id': notifiable_event.id}
                ))
        
        return len(events) > 0
        
    except Exception as e:
        logger.error(f"Error in handle_product_updated: {e}", exc_info=True)
        return False
