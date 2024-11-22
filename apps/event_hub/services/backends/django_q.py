import logging
from typing import Dict, Callable
from django_q.tasks import async_task
from ..event_bus import EventBusBackend
from django.conf import settings
from django.utils.module_loading import import_string

logger = logging.getLogger(__name__)

def execute_listener(listener_module: str, listener_name: str, payload: Dict) -> None:
    """
    Execute a listener function by importing it dynamically.
    This function needs to be at module level to be pickleable.
    """
    logger.info(f"[execute_listener] Starting execution for {listener_module}.{listener_name}")
    try:
        import importlib
        logger.info(f"[execute_listener] Importing module {listener_module}")
        module = importlib.import_module(listener_module)
        
        logger.info(f"[execute_listener] Getting function {listener_name}")
        listener = getattr(module, listener_name)
        
        logger.info(f"[execute_listener] Executing listener with payload: {payload}")
        result = listener(payload)
        
        logger.info(f"[execute_listener] Execution completed with result: {result}")
        return result
        
    except Exception as e:
        logger.exception(f"[execute_listener] Failed to execute listener: {str(e)}")
        raise


class DjangoQBackend(EventBusBackend):
    def enqueue_task(self, listener: Callable, payload: Dict) -> None:
        """Enqueue a task to be executed asynchronously"""
        try:
            logger.info(f"[DjangoQBackend] Enqueueing task for {listener.__name__}")
            
            # Get the module and function name for the listener
            listener_module = listener.__module__
            listener_name = listener.__name__
            
            logger.info(f"[DjangoQBackend] Module: {listener_module}, Function: {listener_name}")
            
            # Queue the task using the module-level function
            task_id = async_task(
                execute_listener,  # Call the function directly
                listener_module,
                listener_name,
                payload,
                task_name=f"event.{listener_name}",
                hook='apps.event_hub.services.backends.django_q.task_hook',
                timeout=getattr(settings, 'EVENT_BUS_TASK_TIMEOUT', 300),
            )
            
            logger.info(f"[DjangoQBackend] Task {task_id} enqueued successfully")
            
        except Exception as e:
            logger.exception(f"[DjangoQBackend] Failed to enqueue task: {str(e)}")
            raise

    def execute_task_sync(self, listener: Callable, payload: Dict) -> None:
        """Execute the listener synchronously"""
        try:
            logger.info(f"[DjangoQBackend] Executing {listener.__name__} synchronously")
            result = listener(payload)
            logger.info(f"[DjangoQBackend] Sync execution completed: {result}")
            
        except Exception as e:
            logger.exception(f"[DjangoQBackend] Sync execution failed: {str(e)}")
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
    logger.info(f"[task_hook] Task completed: {task.id}")
    logger.info(f"[task_hook] Function: {task.func}")
    logger.info(f"[task_hook] Args: {task.args}")
    logger.info(f"[task_hook] Result: {task.result}")
    
    if task.success:
        logger.info("[task_hook] Task succeeded")
    else:
        logger.error(f"[task_hook] Task failed: {task.result}")