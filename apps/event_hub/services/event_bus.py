from typing import Dict, List, Callable
import logging
from .backends.base import EventBusBackend
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from ..events import EventTypes
import time

logger = logging.getLogger(__name__)

class EventBus:
    _instance = None
    _initialized = False
    _listeners: Dict[str, List[Callable]] = {}

    def __new__(cls, backend=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, backend: EventBusBackend = None):
        if not self._initialized:
            if backend is None:
                raise ValueError("Backend must be provided for EventBus initialization")
            self.backend = backend
            self._initialized = True

    def register_listener(self, event_name: str, listener: Callable) -> None:
        if event_name not in self._listeners:
            self._listeners[event_name] = []
        self._listeners[event_name].append(listener)
        logger.debug(f"Registered listener {listener.__name__} for event {event_name}")

    def emit_event(self, event_type: str, payload: dict, is_async: bool = True) -> None:
        # Validate event type
        if not EventTypes.validate_event(event_type):
            logger.error(f"Invalid event type: {event_type}")
            return
        
        # Log the event
        event_log = EventLog.objects.create(
            event_type=event_type,
            payload=payload
        )
        
        if event_type not in self._listeners:
            logger.warning(f"No listeners registered for event {event_type}")
            return

        start_time = time.time()
        
        try:
            for listener in self._listeners[event_type]:
                if is_async:
                    self.backend.enqueue_task(listener, payload)
                else:
                    self.backend.execute_task_sync(listener, payload)
            
            event_log.processed = True
            event_log.processing_time = time.time() - start_time
            event_log.save()
            
        except Exception as e:
            event_log.error = str(e)
            event_log.save()
            self.backend.report_error(e, {
                'event_type': event_type,
                'listener': listener.__name__,
                'payload': payload
            })
            raise
