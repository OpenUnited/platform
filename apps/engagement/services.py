from typing import Optional
from django.utils import timezone
from django.db.models import QuerySet

from apps.engagement.models import (
    NotifiableEvent,
    AppNotification,
    EmailNotification,
    NotificationPreference
)
from apps.capabilities.talent.models import Person


class NotificationService:
    def get_unread_notifications(self, person: Person) -> QuerySet[AppNotification]:
        """Get all unread app notifications for a person"""
        return AppNotification.objects.filter(
            event__person=person,
            is_read=False
        ).select_related('event').order_by('-created_at')

    def get_all_notifications(
        self, 
        person: Person, 
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> QuerySet[AppNotification]:
        """Get all app notifications for a person with optional pagination"""
        notifications = AppNotification.objects.filter(
            event__person=person
        ).select_related('event').order_by('-created_at')

        if offset is not None:
            notifications = notifications[offset:]
        if limit is not None:
            notifications = notifications[:limit]
        
        return notifications

    def mark_notification_as_read(self, notification_id: int, person: Person) -> bool:
        """Mark a specific notification as read if it belongs to the person"""
        try:
            notification = AppNotification.objects.get(
                id=notification_id,
                event__person=person
            )
            notification.mark_as_read()
            return True
        except AppNotification.DoesNotExist:
            return False

    def mark_all_as_read(self, person: Person) -> int:
        """Mark all unread notifications as read for a person"""
        now = timezone.now()
        return AppNotification.objects.filter(
            event__person=person,
            is_read=False
        ).update(is_read=True, read_at=now)

    def get_notification_count(self, person: Person) -> int:
        """Get count of unread notifications"""
        return AppNotification.objects.filter(
            event__person=person,
            is_read=False
        ).count()

    def get_recent_notifications(self, person: Person, limit: int = 5) -> QuerySet[AppNotification]:
        """Get most recent notifications regardless of read status"""
        return AppNotification.objects.filter(
            event__person=person
        ).select_related('event').order_by('-created_at')[:limit]

    def update_notification_preferences(
        self, 
        person: Person, 
        product_notifications: str
    ) -> NotificationPreference:
        """Update notification preferences for a person"""
        prefs, _ = NotificationPreference.objects.get_or_create(person=person)
        prefs.product_notifications = product_notifications
        prefs.save()
        return prefs

    def get_email_history(
        self, 
        person: Person,
        days: int = 30
    ) -> QuerySet[EmailNotification]:
        """Get email notification history for a person"""
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return EmailNotification.objects.filter(
            event__person=person,
            sent_at__gte=cutoff
        ).select_related('event').order_by('-sent_at')

    def cleanup_old_notifications(self) -> tuple[int, int]:
        """
        Clean up notifications past their delete_at date
        Returns tuple of (app_notifications_deleted, email_notifications_deleted)
        """
        now = timezone.now()
        app_deleted = AppNotification.objects.filter(delete_at__lte=now).delete()[0]
        email_deleted = EmailNotification.objects.filter(delete_at__lte=now).delete()[0]
        NotifiableEvent.objects.filter(delete_at__lte=now).delete()
        
        return app_deleted, email_deleted

