import logging
from typing import Union, Dict, Callable
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

logger = logging.getLogger(__name__)

def execute_listener(listener_module: str, listener_name: str, payload: Dict) -> None:
    """
    Execute a listener function by importing it dynamically.
    This function needs to be at module level to be pickleable.
    """
    try:
        import importlib
        from django.utils import timezone
        from apps.event_hub.models import EventLog
        
        # Get event log before execution
        event_log = EventLog.objects.filter(payload=payload).first()
        if not event_log:
            logger.error(f"No event log found for payload: {payload}")
            return
            
        # Import and execute the listener
        if isinstance(listener_module, str):
            module = importlib.import_module(listener_module)
            listener = getattr(module, listener_name)
        else:
            listener = listener_module
        
        start_time = timezone.now()
        result = listener(payload)
        
        # Update event log
        processing_time = (timezone.now() - start_time).total_seconds()
        if event_log:
            event_log.processed = True
            event_log.processing_time = processing_time
            event_log.save(update_fields=['processed', 'processing_time'])
        
        return result
        
    except Exception as e:
        logger.exception(f"Error executing listener: {str(e)}")
        if event_log:
            event_log.error = str(e)
            event_log.save(update_fields=['error'])
        raise


class DjangoQBackend(EventBusBackend):
    def enqueue_task(self, listener: Union[str, Callable], payload: Dict, event_type: str) -> str:
        """
        Enqueues a task for execution
        
        Args:
            listener: Function or import path to execute
            payload: Data to pass to the function
            event_type: The type of event being processed (e.g. "product.created")
        """
        try:
            from apps.event_hub.models import EventLog

            # Check if we're in test mode
            if getattr(settings, 'DJANGO_Q', {}).get('sync', False):
                # Create event log before execution
                event_log = EventLog.objects.create(
                    payload=payload,
                    processed=False,
                    event_type=event_type
                )
                
                start_time = timezone.now()
                
                # Execute the listener
                if isinstance(listener, str):
                    module_path, function_name = listener.rsplit('.', 1)
                    module = __import__(module_path, fromlist=[function_name])
                    listener = getattr(module, function_name)
                
                result = listener(payload)
                
                # Update event log
                event_log.processed = True
                event_log.processing_time = (timezone.now() - start_time).total_seconds()
                event_log.save(update_fields=['processed', 'processing_time'])
                
                return 'sync-executed'

            # For async execution...
            task_id = async_task(
                listener if not isinstance(listener, str) else import_string(listener),
                payload,
                event_type=event_type
            )
            return task_id

        except Exception as e:
            logger.exception(f"[DjangoQBackend] Failed to enqueue task: {str(e)}")
            raise

    def execute_task_sync(self, listener: Union[str, Callable], payload: Dict, event_type: str) -> None:
        """Execute the listener synchronously"""
        try:
            from apps.event_hub.models import EventLog
            
            # Get event log before execution
            event_log = EventLog.objects.filter(payload=payload).first()
            if not event_log:
                logger.error(f"No event log found for payload: {payload}")
                return
            
            start_time = timezone.now()
            
            # Execute listener
            if isinstance(listener, str):
                module_path, function_name = listener.rsplit('.', 1)
                module = __import__(module_path, fromlist=[function_name])
                listener = getattr(module, function_name)
            result = listener(payload)
            
            # Update event log
            processing_time = (timezone.now() - start_time).total_seconds()
            event_log.processed = True
            event_log.processing_time = processing_time
            event_log.save(update_fields=['processed', 'processing_time'])
            
            return result
        except Exception as e:
            logger.exception(f"[DjangoQBackend] Sync execution failed: {str(e)}")
            if event_log:
                event_log.error = str(e)
                event_log.save(update_fields=['error'])
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
    logger.info(f"Task {task.id} completed with status: {task.success}")
    
    if task.success:
        # Update event log if it exists
        from apps.event_hub.models import EventLog
        if isinstance(task.args, tuple) and len(task.args) > 0:
            payload = task.args[-1] if isinstance(task.args[-1], dict) else None
            if payload:
                event_log = EventLog.objects.filter(payload=payload).first()
                if event_log and not event_log.processed:
                    event_log.processed = True
                    event_log.processing_time = (task.stopped - task.started).total_seconds()
                    event_log.save(update_fields=['processed', 'processing_time'])
    else:
        logger.error(f"Task failed with error: {task.result}")
        if hasattr(task.result, '__traceback__'):
            logger.error(f"Traceback: {task.result.__traceback__}")