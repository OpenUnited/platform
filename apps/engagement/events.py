from typing import Dict
import logging
from django_q.tasks import async_task
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

def handle_product_created(event_payload):
    """Handle product created event"""
    try:
        # Extract required fields
        product_id = event_payload.get('product_id')
        person_id = event_payload.get('person_id')
        
        # Get notification preferences - use get() instead of filter() since we want exact match
        try:
            preferences = NotificationPreference.objects.get(
                person_id=person_id,
                product_notifications__in=[
                    NotificationPreference.Type.BOTH,
                    NotificationPreference.Type.APPS,
                    NotificationPreference.Type.EMAIL
                ]
            )
        except NotificationPreference.DoesNotExist:
            logger.info(f"No matching preferences found for person {person_id}")
            return True

        # Create the notifiable event
        event = NotifiableEvent.objects.create(
            event_type=EventTypes.PRODUCT_CREATED,
            person_id=person_id,
            params=event_payload
        )
        
        try:
            # Create app notification if enabled
            if preferences.product_notifications in [NotificationPreference.Type.APPS, NotificationPreference.Type.BOTH]:
                try:
                    app_template = AppNotificationTemplate.objects.get(
                        event_type=EventTypes.PRODUCT_CREATED
                    )
                    AppNotification.objects.create(
                        event=event,
                        title=app_template.render_title(event_payload),
                        message=app_template.render_template(event_payload)
                    )
                except (AppNotificationTemplate.DoesNotExist, Exception) as e:
                    logger.error(f"Error with app notification: {e}")
                    AppNotification.objects.create(
                        event=event,
                        title="New Product Created",
                        message="There was an error processing this notification."
                    )
            
            # Create email notification if enabled
            if preferences.product_notifications in [NotificationPreference.Type.EMAIL, NotificationPreference.Type.BOTH]:
                try:
                    email_template = EmailNotificationTemplate.objects.get(
                        event_type=EventTypes.PRODUCT_CREATED
                    )
                    EmailNotification.objects.create(
                        event=event,
                        title=email_template.render_title(event_payload),
                        body=email_template.render_template(event_payload)
                    )
                except (EmailNotificationTemplate.DoesNotExist, Exception) as e:
                    logger.error(f"Error with email notification: {e}")
                    EmailNotification.objects.create(
                        event=event,
                        title="New Product Created",
                        body="There was an error processing this notification."
                    )
                    
        except Exception as e:
            logger.error(f"Error creating notifications: {e}")
            # Always create at least one notification
            AppNotification.objects.create(
                event=event,
                title="New Product Created",
                message="There was an error processing this notification."
            )
            
        return True
        
    except Exception as e:
        logger.error(f"Error in handle_product_created: {e}", exc_info=True)
        raise

def handle_product_updated(event_data):
    """Handle product updated event"""
    logger.info(f"Handling product updated event: {event_data}")
    
    # Create the event
    event = NotifiableEvent.objects.create(
        event_type=EventTypes.PRODUCT_UPDATED,
        person_id=event_data['person_id'],
        params=event_data
    )
    logger.info(f"Created event: {event}")
    
    # Queue the async task
    async_result = async_task('apps.engagement.tasks.process_notification', event.id)
    logger.info(f"Queued async task: {async_result}")
    
    return event

def process_event(event_id):
    """Process the notification event"""
    logger.info(f"Processing event {event_id}")
    try:
        event = NotifiableEvent.objects.get(id=event_id)
        logger.info(f"Found event: {event}")
        
        # Get notification preferences
        prefs = NotificationPreference.objects.get(person=event.person)
        logger.info(f"Found preferences: {prefs.product_notifications}")
        
        # Get templates
        app_template = AppNotificationTemplate.objects.get(event_type=event.event_type)
        email_template = EmailNotificationTemplate.objects.get(event_type=event.event_type)
        logger.info(f"Found templates: app={app_template}, email={email_template}")
        
        # Create notifications
        if prefs.product_notifications in [NotificationPreference.Type.APP, NotificationPreference.Type.BOTH]:
            app_notif = AppNotification.objects.create(
                event=event,
                title=app_template.render_title(event.params),
                message=app_template.render_template(event.params)
            )
            logger.info(f"Created app notification: {app_notif}")
            
        if prefs.product_notifications in [NotificationPreference.Type.EMAIL, NotificationPreference.Type.BOTH]:
            email_notif = EmailNotification.objects.create(
                event=event,
                title=email_template.render_title(event.params),
                body=email_template.render_template(event.params)
            )
            logger.info(f"Created email notification: {email_notif}")
            
    except Exception as e:
        logger.error(f"Error processing event {event_id}: {e}", exc_info=True)
        raise