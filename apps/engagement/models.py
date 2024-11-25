from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import timedelta
from apps.common.mixins import TimeStampMixin
from apps.event_hub.events import EventTypes
import logging

logger = logging.getLogger(__name__)


def default_delete_at():
    return timezone.now() + timedelta(hours=72)


class NotifiableEvent(TimeStampMixin):
    """An event that occurred that a person could be notified about"""
    event_type = models.CharField(
        max_length=50, 
        choices=EventTypes.choices(),
        db_index=True
    )
    person = models.ForeignKey('talent.Person', on_delete=models.CASCADE)
    params = models.JSONField(default=dict)
    delete_at = models.DateTimeField(default=default_delete_at)

    class Meta:
        indexes = [
            models.Index(fields=['delete_at']),
            models.Index(fields=['person']),
        ]

    def __str__(self):
        return f"{self.get_event_type_display()} for {self.person}"


class EmailNotificationTemplate(models.Model):
    """Email notification templates for different event types"""
    event_type = models.CharField(
        max_length=50, 
        choices=EventTypes.choices(),
        primary_key=True
    )
    title = models.CharField(max_length=400)
    template = models.CharField(max_length=4000)
    permitted_params = models.CharField(max_length=500)

    def clean(self):
        _template_is_valid(self.title, self.permitted_params)
        _template_is_valid(self.template, self.permitted_params)

    def __str__(self):
        return f"Email template for {self.get_event_type_display()}"

    def render_title(self, params):
        try:
            return self.title.format(**params)
        except Exception as e:
            logger.error(f"Error rendering email notification title: {e}")
            return "Notification"

    def render_template(self, params):
        try:
            return self.template.format(**params)
        except Exception as e:
            logger.error(f"Error rendering email notification template: {e}")
            return "There was an error creating this notification."


def _template_is_valid(template, permitted_params):
    permitted_params_list = permitted_params.split(",")
    params = {param: "" for param in permitted_params_list}
    try:
        template.format(**params)
    except IndexError:
        raise ValidationError({"template": _("No curly brace without a name permitted")}) from None
    except KeyError as ke:
        raise ValidationError(
            {
                "template": _(
                    f"{ke.args[0]} isn't a permitted param for template. Please use one of these: {permitted_params}"
                )
            }
        ) from None


class NotificationPreference(TimeStampMixin):
    class Type(models.TextChoices):
        NONE = "NONE", "No notifications"
        APPS = "APPS", "In-app only"
        EMAIL = "EMAIL", "Email only"
        BOTH = "BOTH", "Both app and email"

    person = models.OneToOneField(
        "talent.Person",
        on_delete=models.CASCADE,
        related_name="notification_preferences"
    )
    product_notifications = models.CharField(
        max_length=10,
        choices=Type.choices,
        default=Type.BOTH
    )

    class Meta:
        verbose_name_plural = "Notification Preferences"
        indexes = [
            models.Index(fields=['person'])
        ]

    def __str__(self):
        return f"Notification Preferences for {self.person}"

    def get_channel_for_event(self, event_type: str) -> str:
        """Maps event types to their corresponding preference field"""
        return self.product_notifications


class EmailNotification(TimeStampMixin):
    """Record of emails sent to users"""
    event = models.ForeignKey(NotifiableEvent, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=400)
    body = models.CharField(max_length=4000, null=True, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    delete_at = models.DateTimeField(default=default_delete_at)

    class Meta:
        indexes = [
            models.Index(fields=['event']),
            models.Index(fields=['sent_at']),
            models.Index(fields=['delete_at']),
        ]

    def __str__(self):
        return f"Email notification for {self.event}"


class AppNotification(TimeStampMixin):
    """Notifications to be displayed in the web app"""
    event = models.ForeignKey(NotifiableEvent, on_delete=models.CASCADE)
    title = models.CharField(max_length=400)
    message = models.CharField(max_length=4000)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    delete_at = models.DateTimeField(default=default_delete_at)

    class Meta:
        indexes = [
            models.Index(fields=['event']),
            models.Index(fields=['is_read']),
            models.Index(fields=['read_at']),
            models.Index(fields=['delete_at']),
        ]

    def __str__(self):
        return f"App notification for {self.event}"

    def mark_as_read(self):
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=['is_read', 'read_at'])


class AppNotificationTemplate(models.Model):
    """Templates for in-app notifications"""
    event_type = models.CharField(
        max_length=50, 
        choices=EventTypes.choices(),
        primary_key=True
    )
    title = models.CharField(max_length=400)
    template = models.CharField(max_length=4000)
    permitted_params = models.CharField(max_length=500)

    def clean(self):
        _template_is_valid(self.title, self.permitted_params)
        _template_is_valid(self.template, self.permitted_params)

    def __str__(self):
        return f"App notification template for {self.get_event_type_display()}"

    def render_title(self, params):
        try:
            return self.title.format(**params)
        except Exception as e:
            logger.error(f"Error rendering app notification title: {e}")
            return "Notification"

    def render_template(self, params):
        try:
            return self.template.format(**params)
        except Exception as e:
            logger.error(f"Error rendering app notification template: {e}")
            return "There was an error processing this notification."
