import logging
from apps.engagement.models import (
    NotifiableEvent,
    AppNotification,
    EmailNotification,
    AppNotificationTemplate,
    EmailNotificationTemplate,
    NotificationPreference
)
from django.db import transaction

logger = logging.getLogger(__name__)

def process_notification(event_type=None, payload=None):
    """Process a notification event and create notifications based on preferences"""
    try:
        logger.debug(f"Processing notification with payload: {payload}")
        
        event_id = payload.get('event_id')
        if not event_id:
            logger.error("No event_id in payload")
            return False
            
        with transaction.atomic():
            try:
                event = NotifiableEvent.objects.select_for_update().get(id=event_id)
                person = event.person
                
                # Get or create notification preferences with default BOTH
                prefs, created = NotificationPreference.objects.get_or_create(
                    person=person,
                    defaults={'product_notifications': NotificationPreference.Type.BOTH}
                )
                
                if created:
                    logger.info(f"Created default notification preferences for person {person.id}")
                
                # Get notification type based on preferences
                notification_type = prefs.product_notifications
                
                if notification_type in [NotificationPreference.Type.APPS, NotificationPreference.Type.BOTH]:
                    try:
                        template = AppNotificationTemplate.objects.get(event_type=event.event_type)
                        
                        try:
                            title = template.title.format(**event.params)
                            message = template.template.format(**event.params)
                        except KeyError as e:
                            logger.error(f"Missing template parameter: {e}")
                            title = "Notification Error"
                            message = "There was an error processing this notification."
                            
                        AppNotification.objects.create(
                            notifiable_event=event,
                            person=person,
                            title=title,
                            message=message
                        )
                    except AppNotificationTemplate.DoesNotExist:
                        logger.error(f"No app template found for event type: {event.event_type}")
                        # Create default notification when template is missing
                        AppNotification.objects.create(
                            notifiable_event=event,
                            person=person,
                            title="System Notification",
                            message="There was an error processing this notification."
                        )
                        
                if notification_type in [NotificationPreference.Type.EMAIL, NotificationPreference.Type.BOTH]:
                    try:
                        template = EmailNotificationTemplate.objects.get(event_type=event.event_type)
                        
                        try:
                            title = template.title.format(**event.params)
                            body = template.template.format(**event.params)
                        except KeyError as e:
                            logger.error(f"Missing template parameter: {e}")
                            title = "Notification Error"
                            body = "There was an error processing this notification."
                            
                        EmailNotification.objects.create(
                            notifiable_event=event,
                            person=person,
                            title=title,
                            body=body
                        )
                    except EmailNotificationTemplate.DoesNotExist:
                        logger.error(f"No email template found for event type: {event.event_type}")
                        # Create default notification when template is missing
                        EmailNotification.objects.create(
                            notifiable_event=event,
                            person=person,
                            title="System Notification",
                            body="A notification was generated but the template was not found."
                        )
                        
                return True
                
            except NotifiableEvent.DoesNotExist:
                logger.error(f"Event {event_id} not found")
                return False
            
    except Exception as e:
        logger.error(f"Error processing notification: {str(e)}")
        return False
