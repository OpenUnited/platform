import os
import django
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Import after Django setup
from django_q.models import Task
from django_q.brokers import get_broker
from apps.engagement.models import (
    NotifiableEvent,
    AppNotification,
    EmailNotification
)
from apps.event_hub.models import EventLog

def clear_transient_events():
    """
    Development utility to clear all transient events, notifications, and event logs.
    """
    deleted_counts = {}

    # Clear each type of record independently
    try:
        deleted_counts['event_logs'] = EventLog.objects.all().delete()[0]
        print("Cleared event logs")
    except Exception as e:
        print(f"Error clearing event logs: {str(e)}")

    try:
        deleted_counts['app_notifications'] = AppNotification.objects.all().delete()[0]
        print("Cleared app notifications")
    except Exception as e:
        print(f"Error clearing app notifications: {str(e)}")

    try:
        deleted_counts['email_notifications'] = EmailNotification.objects.all().delete()[0]
        print("Cleared email notifications")
    except Exception as e:
        print(f"Error clearing email notifications: {str(e)}")

    try:
        deleted_counts['notifiable_events'] = NotifiableEvent.objects.all().delete()[0]
        print("Cleared notifiable events")
    except Exception as e:
        print(f"Error clearing notifiable events: {str(e)}")

    try:
        deleted_counts['tasks'] = Task.objects.all().delete()[0]
        print("Cleared tasks")
    except Exception as e:
        print(f"Error clearing tasks: {str(e)}")

    try:
        broker = get_broker()
        broker.purge_queue()
        print("Cleared broker queue")
    except Exception as e:
        print(f"Error clearing broker queue: {str(e)}")

    print("\nFinal deletion counts:")
    for model, count in deleted_counts.items():
        print(f"- {model}: {count}")

if __name__ == '__main__':
    clear_transient_events()