from typing import Dict
import logging
from apps.capabilities.security.services import RoleService
from apps.capabilities.commerce.models import Organisation
from apps.engagement.models import NotifiableEvent
from apps.capabilities.talent.models import Person
from apps.engagement.models import NotificationPreference, AppNotificationTemplate, AppNotification
from apps.capabilities.security.models import OrganisationPersonRoleAssignment
from apps.capabilities.commerce.models import Product

logger = logging.getLogger(__name__)

def handle_product_created(payload: dict) -> None:
    """Handle product.created event"""
    logger.info(f"Processing product created event: {payload}")
    try:
        product_id = payload.get('product_id')
        if not product_id:
            logger.error("No product_id in payload")
            return
            
        product = Product.objects.get(id=product_id)
        
        params = {
            'name': payload.get('name', product.name),
            'url': payload.get('url', f'/products/{product.id}/summary/')
        }
        
        # Always notify the creator
        person_id = payload.get('person_id')
        if person_id:
            creator = Person.objects.get(id=person_id)
            event = NotifiableEvent.objects.create(
                event_type=NotifiableEvent.EventType.PRODUCT_CREATED,
                person=creator,
                params=params
            )
            _create_notifications_for_event(event)
        
        # If org-owned, also notify org admins
        if product.is_owned_by_organisation():
            admin_assignments = OrganisationPersonRoleAssignment.objects.filter(
                organisation=product.organisation,
                role__in=[
                    OrganisationPersonRoleAssignment.OrganisationRoles.OWNER,
                    OrganisationPersonRoleAssignment.OrganisationRoles.MANAGER
                ]
            ).exclude(person_id=person_id)  # Don't double-notify the creator
            
            for assignment in admin_assignments:
                event = NotifiableEvent.objects.create(
                    event_type=NotifiableEvent.EventType.PRODUCT_CREATED,
                    person=assignment.person,
                    params=params
                )
                _create_notifications_for_event(event)
                
    except Exception as e:
        logger.error(f"Error processing product created event: {str(e)}")
        raise

def _create_notifications_for_event(event: NotifiableEvent) -> None:
    """Create notifications based on user preferences"""
    try:
        prefs = NotificationPreference.objects.get(person=event.person)
        if prefs.product_notifications in [NotificationPreference.Type.APPS, NotificationPreference.Type.BOTH]:
            template = AppNotificationTemplate.objects.get(event_type=event.event_type)
            AppNotification.objects.create(
                event=event,
                title=template.title_template.format(**event.params),
                message=template.message_template.format(**event.params)
            )
    except NotificationPreference.DoesNotExist:
        logger.warning(f"No notification preferences found for person {event.person.id}")
    except AppNotificationTemplate.DoesNotExist:
        logger.error(f"No app notification template found for event type {event.event_type}")
    except Exception as e:
        logger.error(f"Error creating notifications for event: {str(e)}")