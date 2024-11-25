from typing import Dict, List, Callable, Union
import logging
from .backends.base import EventBusBackend
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from ..events import EventTypes
from ..models import EventLog
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

    def register_listener(self, event_name: str, listener: Union[Callable, str]) -> None:
        """Register a listener for an event type
        
        Args:
            event_name: The event type to listen for
            listener: Either a callable function or a string path to the listener
        """
        if event_name not in self._listeners:
            self._listeners[event_name] = []
        self._listeners[event_name].append(listener)
        
        # Get listener name for logging
        if isinstance(listener, str):
            listener_name = listener.split('.')[-1]  # Get last part of path
        else:
            listener_name = getattr(listener, '__name__', str(listener))
        
        logger.debug(f"Registered listener {listener_name} for event {event_name}")

    def emit_event(self, event_type: str, payload: Dict):
        """Emit an event to all registered listeners"""
        if not EventTypes.validate_event(event_type):
            raise ValueError(f"Invalid event type: {event_type}")

        listeners = self._listeners.get(event_type, [])
        for listener in listeners:
            try:
                # Pass the event_type to the backend
                self.backend.enqueue_task(listener, payload, event_type)
            except Exception as e:
                logger.error(f"Failed to enqueue task for {listener}: {e}")
