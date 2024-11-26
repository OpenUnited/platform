from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta

from apps.common import settings
from .events import EventTypes

class EventLog(models.Model):
    """Log of all events that pass through the event bus"""
    
    event_type = models.CharField(max_length=100)
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    error = models.TextField(null=True, blank=True)
    parent_event_id = models.IntegerField(null=True, blank=True)
    
    class Meta:
        indexes = [
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
        super().save(*args, **kwargs)
