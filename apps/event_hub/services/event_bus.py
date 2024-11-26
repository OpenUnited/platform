from typing import Dict, Callable
import logging
from collections import defaultdict
import pickle
from django.core.cache import cache

from apps.event_hub.models import EventLog

logger = logging.getLogger(__name__)

def process_event_task(event_type: str, data: Dict) -> None:
    """Standalone function to process events in worker process"""
    logger.info(f"Processing event {event_type}")
    payload = data['payload']
    listener_paths = data['listener_paths']
    
    for path in listener_paths:
        try:
            logger.info(f"Importing listener from path: {path}")
            module_path, function_name = path.rsplit('.', 1)
            module = __import__(module_path, fromlist=[function_name])
            listener = getattr(module, function_name)
            
            logger.info(f"Executing listener: {listener}")
            listener(event_type=event_type, payload=payload)
        except Exception as e:
            logger.error(f"Error executing listener {path}: {e}", exc_info=True)

class EventBus:
    """
    Event bus implementation that delegates to a configured backend.
    """
    def __init__(self, backend):
        self.backend = backend  # Store the backend instance
        self.listeners: Dict[str, set[Callable]] = defaultdict(set)
        # Try to load listeners from cache
        self._load_listeners()

    def register_listener(self, event_type: str, listener: Callable) -> None:
        """
        Register a listener for a specific event type.

        Args:
            event_type: The type of event to listen for.
            listener: Function to execute when the event occurs.
        """
        if listener not in self.listeners[event_type]:
            self.listeners[event_type].add(listener)
            # Store the listener's import path instead of the callable
            listener_path = f"{listener.__module__}.{listener.__name__}"
            cached_listeners = cache.get('event_bus_listeners', {})
            if event_type not in cached_listeners:
                cached_listeners[event_type] = set()
            cached_listeners[event_type].add(listener_path)
            cache.set('event_bus_listeners', cached_listeners)
            logger.debug(f"Registered listener {listener_path} for event {event_type}")

    def _load_listeners(self):
        """Load listeners from cache"""
        cached_listeners = cache.get('event_bus_listeners', {})
        for event_type, listener_paths in cached_listeners.items():
            for path in listener_paths:
                try:
                    module_path, function_name = path.rsplit('.', 1)
                    module = __import__(module_path, fromlist=[function_name])
                    listener = getattr(module, function_name)
                    self.listeners[event_type].add(listener)
                    logger.debug(f"Loaded listener {path} for event {event_type}")
                except Exception as e:
                    logger.error(f"Failed to load listener {path}: {e}")

    def publish(self, event_type: str, payload: Dict) -> None:
        logger.info(f"Publishing event {event_type}")
        if event_type not in self.listeners:
            logger.warning(f"No listeners registered for event type: {event_type}")
            return
        
        # Get the import paths for all listeners
        listener_paths = [
            f"{listener.__module__}.{listener.__name__}"
            for listener in self.listeners[event_type]
        ]
        
        logger.info(f"Enqueueing task with listener paths: {listener_paths}")
        
        self.backend.enqueue_task(
            process_event_task,  # Use the standalone function instead of self.process_event
            {
                'payload': payload,
                'listener_paths': listener_paths
            },
            event_type
        )

    def execute_task_sync(self, listener: Callable, payload: Dict, event_type: str) -> None:
        """
        Execute a listener synchronously. This might be used in testing or where immediate execution is required.

        Args:
            listener: Function to execute.
            payload: Data to pass to the function.
            event_type: The type of event being processed.
        """
        try:
            listener(event_type=event_type, payload=payload)
            logger.debug(f"Executed listener {listener} synchronously for event {event_type}")
        except Exception as e:
            logger.error(f"Error executing listener {listener} synchronously for event {event_type}: {e}")
            raise
