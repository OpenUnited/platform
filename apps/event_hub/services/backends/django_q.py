import logging
from typing import Union, Dict, Callable, Any, Optional
from django_q.tasks import async_task
from .base import EventBusBackend
from django.conf import settings
from django.utils.module_loading import import_string
from django.db import transaction
from django_q.models import Schedule
from django_q.models import Task
from django_q.signing import SignedPackage
from django.utils import timezone
import time
import threading
from django_q.brokers import get_broker
from apps.event_hub.models import EventLog
from apps.event_hub.events import EventTypes

logger = logging.getLogger(__name__)

def _create_event_log(event_data: Dict, event_type: str, parent_event_id: Optional[int] = None) -> EventLog:
    """Create an event log entry"""
    return EventLog.objects.create(
        event_type=event_type,
        payload=event_data,
        parent_event_id=parent_event_id
    )

def _execute_listener(listener: Union[str, Callable], event_data: Dict, event_type: str = None) -> Any:
    """Execute a listener function"""
    if isinstance(listener, str):
        logger.info(f"Importing listener from path: {listener}")
        module_path, function_name = listener.rsplit('.', 1)
        module = __import__(module_path, fromlist=[function_name])
        listener = getattr(module, function_name)
    
    try:
        # Add event_type to event data
        event_data = event_data.copy()
        event_data['event_type'] = event_type
        return listener(event_type=event_type, payload=event_data)
    except Exception as e:
        logger.error(f"Error executing listener: {str(e)}", exc_info=True)
        raise

class DjangoQBackend(EventBusBackend):
    def enqueue_task(self, listener: Union[str, Callable], event_data: Dict, event_type: str) -> str:
        """Enqueues a task for execution"""
        try:
            # Create event log
            event_log = _create_event_log(event_data['payload'], event_type)
            
            # Convert callable to string path if needed
            if not isinstance(listener, str):
                listener = f"{listener.__module__}.{listener.__name__}"
            
            # Enqueue the task
            task_id = async_task(
                listener,
                event_type=event_type,
                data={
                    'event_id': event_log.id,
                    'payload': event_data['payload'],
                    'listener_paths': event_data['listener_paths']
                }
            )
            
            logger.info(f"Task enqueued with ID: {task_id} for event_log: {event_log.id}")
            return task_id

        except Exception as e:
            logger.error(f"Error in enqueue_task: {str(e)}", exc_info=True)
            self.report_error(e, {'listener': listener, 'event_data': event_data, 'event_type': event_type})
            raise

    def execute_task_sync(self, listener: Union[str, Callable], payload: Dict, event_type: str) -> None:
        """Execute the listener synchronously"""
        logger.info(f"execute_task_sync called")
        try:
            event_log = _create_event_log(payload, event_type)
            start_time = timezone.now()
            
            result = _execute_listener(listener, payload, event_type)
            
            return result
        except Exception as e:
            self.report_error(e, {'listener': listener, 'payload': payload})
            raise

    def report_error(self, error: Exception, context: Dict) -> None:
        """Report error to monitoring system"""
        error_message = f"Error in Django-Q backend: {str(error)}"
        
        # Add more context to error reporting
        error_context = {
            "error_type": error.__class__.__name__,
            "error_message": str(error),
            "context": context,
            "backend": "django_q"
        }
        
        logger.error(error_message, extra=error_context, exc_info=True)
        
        # Optional: Add custom error reporting (e.g., Sentry)
        if hasattr(settings, 'EVENT_BUS_ERROR_CALLBACK'):
            try:
                error_callback = import_string(settings.EVENT_BUS_ERROR_CALLBACK)
                error_callback(error_message, error_context)
            except Exception as e:
                logger.exception("Failed to execute error callback")


def task_hook(task):
    """Hook that runs after task completion"""
    logger.info(f"Task hook called for task {task.id}")
    logger.info(f"Task args: {task.args}")
    logger.info(f"Task kwargs: {task.kwargs}")
    logger.info(f"Task success: {task.success}")
    
    if task.success:
        logger.info(f"Task result: {task.result}")
        # Task is automatically deleted after this
    else:
        logger.error(f"Task failed with error: {task.result}")