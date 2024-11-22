from typing import Dict, List, Callable
import logging
from .backends.base import EventBusBackend

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

    def emit_event(self, event_name: str, payload: dict, is_async: bool = True) -> None:
        if event_name not in self._listeners:
            logger.warning(f"No listeners registered for event {event_name}")
            return

        for listener in self._listeners[event_name]:
            try:
                if is_async:
                    self.backend.enqueue_task(listener, payload)
                else:
                    self.backend.execute_task_sync(listener, payload)
            except Exception as e:
                logger.error(f"Error processing event {event_name}: {str(e)}")
                self.backend.report_error(e, {
                    'event_name': event_name,
                    'listener': listener.__name__,
                    'payload': payload
                })
                raise  # Re-raise to maintain current behavior
