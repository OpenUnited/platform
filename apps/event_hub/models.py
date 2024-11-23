from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta

from apps.common import settings
from .events import EventTypes

class EventLog(models.Model):
    """Log of all events that pass through the event bus"""
    
    event_type = models.CharField(
        max_length=255,
        choices=EventTypes.choices(),
        db_index=True,
        help_text="Type of event from the centralized event registry"
    )
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    delete_at = models.DateTimeField(db_index=True)
    
    # Tracking fields
    processed = models.BooleanField(default=False)
    error = models.TextField(null=True, blank=True)
    processing_time = models.FloatField(null=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['delete_at', 'processed']),
            models.Index(fields=['event_type', 'created_at']),
        ]
    
    def clean(self):
        """Validate that event_type is registered"""
        if not EventTypes.validate_event(self.event_type):
            raise ValidationError({
                'event_type': f'Event type {self.event_type} is not registered in EventTypes'
            })
    
    def save(self, *args, **kwargs):
        self.clean()
        if not self.delete_at:
            retention_days = getattr(settings, 'EVENT_LOG_RETENTION_DAYS', 30)
            self.delete_at = timezone.now() + timedelta(days=retention_days)
        super().save(*args, **kwargs)
