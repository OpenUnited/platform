from apps.engagement.models import (
    NotifiableEvent,
    AppNotification,
    EmailNotification,
    AppNotificationTemplate,
    EmailNotificationTemplate,
    NotificationPreference
)

def process_notification(event_id):
    """Process a notification event and create notifications based on preferences"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Handle case where event_id might be a dict
        if isinstance(event_id, dict):
            event_id = event_id.get('event_id')
            
        event = NotifiableEvent.objects.get(id=event_id)
        person = event.person
        prefs = NotificationPreference.objects.get(person=person)
        
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
                    event=event,
                    title=title,
                    message=message
                )
            except AppNotificationTemplate.DoesNotExist:
                logger.error(f"No app template found for event type: {event.event_type}")
                # Create default notification when template is missing
                AppNotification.objects.create(
                    event=event,
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
                    event=event,
                    title=title,
                    body=body
                )
            except EmailNotificationTemplate.DoesNotExist:
                logger.error(f"No email template found for event type: {event.event_type}")
                # Create default notification when template is missing
                EmailNotification.objects.create(
                    event=event,
                    title="System Notification",
                    body="A notification was generated but the template was not found."
                )
                
        return True
            
    except Exception as e:
        logger.error(f"Error processing notification: {str(e)}")
        return False
