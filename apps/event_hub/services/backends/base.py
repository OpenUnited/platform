from abc import ABC, abstractmethod
from typing import Union, Dict, Callable
import logging

logger = logging.getLogger(__name__)

class EventBusBackend(ABC):
    @abstractmethod
    def enqueue_task(self, listener: Union[str, Callable], event_data: Dict, event_type: str) -> str:
        """
        Enqueue a task to be executed asynchronously
        
        Args:
            listener: Either a callable or string path to the listener function
            event_data: Event data to pass to the listener
            event_type: The type of event being processed
            
        Returns:
            str: Task ID
        """
        pass

    @abstractmethod
    def execute_task_sync(self, listener: Union[str, Callable], event_data: Dict, event_type: str) -> None:
        """Execute a task synchronously"""
        pass

    @abstractmethod
    def report_error(self, error: Exception, context: Dict = None) -> None:
        """Report error to monitoring system"""
        pass