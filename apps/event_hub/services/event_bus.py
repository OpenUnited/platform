from typing import Dict, List, Callable, Union
import logging
from django.conf import settings
from .backends.base import EventBusBackend
from .backends.django_q import DjangoQBackend
from ..models import EventLog
import importlib

logger = logging.getLogger(__name__)

def get_event_bus():
    return EventBus()

class EventBus:
    """
    Event bus implementation that delegates to a configured backend
    """
    _instance = None
    _backend = None
    _listeners: Dict[str, List[Union[str, Callable]]] = {}

    def __new__(cls, backend=None):
        if cls._instance is None:
            cls._instance = super(EventBus, cls).__new__(cls)
            cls._instance._backend = backend or DjangoQBackend()
            cls._instance._listeners = {}
        return cls._instance

    def register_listener(self, event_type: str, listener: Union[str, Callable]) -> None:
        """
        Register a listener for a specific event type
        
        Args:
            event_type: The type of event to listen for
            listener: Function or import path to execute when event occurs
        """
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        if listener not in self._listeners[event_type]:
            self._listeners[event_type].append(listener)
            logger.debug(f"Registered listener {listener} for event {event_type}")

    def publish(self, event_type: str, payload: Dict) -> List[str]:
        """
        Publish an event to all registered listeners
        
        Args:
            event_type: The type of event being published
            payload: Data to pass to the listeners
            
        Returns:
            List[str]: List of task IDs for the enqueued tasks (or ['sync'] for sync execution)
        """
        # Log the event first
        event_log = EventLog.objects.create(
            event_type=event_type,
            payload=payload,
            processed=False
        )

        if event_type not in self._listeners:
            logger.warning(f"No listeners registered for event type: {event_type}")
            return []

        task_ids = []
        errors = []
        success = False
        
        for listener in self._listeners[event_type]:
            try:
                # Always execute synchronously in test environment
                if getattr(settings, 'TEST', False):
                    if isinstance(listener, str):
                        module_path, function_name = listener.rsplit('.', 1)
                        module = importlib.import_module(module_path)
                        func = getattr(module, function_name)
                    else:
                        func = listener
                    
                    func(payload)
                    task_ids.append('sync')
                    success = True
                else:
                    task_id = self.enqueue_task(listener, payload, event_type)
                    task_ids.append(task_id)
                    success = True
            except Exception as e:
                error_msg = f"Error executing listener {listener} for event {event_type}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
                continue

        event_log.processed = success
        event_log.error = '\n'.join(errors) if errors else None
        event_log.save()
        
        return task_ids

    def enqueue_task(self, listener: Union[str, Callable], payload: Dict, event_type: str) -> str:
        """
        Enqueue a task using the configured backend
        
        Args:
            listener: Function or import path to execute
            payload: Data to pass to the function
            event_type: The type of event being processed
            
        Returns:
            str: Task ID
        """
        return self._backend.enqueue_task(listener, payload, event_type)

    def execute_task_sync(self, listener: Union[str, Callable], payload: Dict, event_type: str) -> None:
        """
        Execute a task synchronously using the configured backend
        
        Args:
            listener: Function or import path to execute
            payload: Data to pass to the function
            event_type: The type of event being processed
        """
        return self._backend.execute_task_sync(listener, payload, event_type)
