from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class EventBusBackend(ABC):
    @abstractmethod
    def enqueue_task(self, task_path, *args, **kwargs):
        pass

    @abstractmethod
    def execute_task_sync(self, task_path, *args, **kwargs):
        pass

    def report_error(self, error, task_info=None):
        logger.error(f"Error in task {task_info}: {error}") 