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
    
    # Add worker process ID for tracking
    import os
    worker_pid = os.getpid()
    print(f"\n[WORKER {worker_pid}] Starting process_notification for event {event_id}")
    logger.info(f"[WORKER {worker_pid}] Starting process_notification for event {event_id}")
    
    result = {
        'success': False,
        'app_notification_created': False,
        'email_notification_created': False,
        'error': None,
        'worker_pid': worker_pid
    }
    
    try:
        # Add more detailed exception handling
        try:
            event = NotifiableEvent.objects.get(id=event_id)
        except NotifiableEvent.DoesNotExist:
            msg = f"Event {event_id} not found"
            logger.error(f"[WORKER {worker_pid}] {msg}")
            result['error'] = msg
            return result
            
        try:
            prefs = NotificationPreference.objects.get(person=event.person)
        except NotificationPreference.DoesNotExist:
            msg = f"Preferences not found for person {event.person_id}"
            logger.error(f"[WORKER {worker_pid}] {msg}")
            result['error'] = msg
            return result

        # Log preference values
        print(f"[WORKER {worker_pid}] Preference type: {prefs.product_notifications}")
        print(f"[WORKER {worker_pid}] Preference type class: {type(prefs.product_notifications)}")
        print(f"[WORKER {worker_pid}] Valid types: {NotificationPreference.Type.choices}")
        
        print("[WORKER DEBUG] Attempting to get templates")
        app_template = AppNotificationTemplate.objects.get(event_type=event.event_type)
        email_template = EmailNotificationTemplate.objects.get(event_type=event.event_type)
        print("[WORKER DEBUG] Found both templates")
        
        # Debug preference check
        print(f"[DEBUG] Checking if {prefs.product_notifications} in {[NotificationPreference.Type.APP, NotificationPreference.Type.BOTH]}")
        
        # Create app notification if enabled
        if prefs.product_notifications in [NotificationPreference.Type.APP, NotificationPreference.Type.BOTH]:
            print("[DEBUG] Creating app notification")
            rendered_title = app_template.render_title(event.params)
            rendered_message = app_template.render_template(event.params)
            print(f"[DEBUG] Rendered title: {rendered_title}")
            print(f"[DEBUG] Rendered message: {rendered_message}")
            
            app_notif = AppNotification.objects.create(
                event=event,
                title=rendered_title,
                message=rendered_message
            )
            print(f"[DEBUG] Created app notification: {app_notif.id}")
            result['app_notification_created'] = True
        
        # Create email notification if enabled
        if prefs.product_notifications in [NotificationPreference.Type.EMAIL, NotificationPreference.Type.BOTH]:
            logger.info("[PROCESS] Creating email notification")
            email_notif = EmailNotification.objects.create(
                event=event,
                title=email_template.render_title(event.params),
                body=email_template.render_template(event.params)
            )
            logger.info(f"[PROCESS] Created email notification: {email_notif.id}")
            result['email_notification_created'] = True
            
        result['success'] = True
        logger.info("[PROCESS] Successfully completed notification processing")
        return result
            
    except Exception as e:
        logger.error(f"[PROCESS] Error processing notification: {str(e)}", exc_info=True)
        result['error'] = str(e)
        return result
