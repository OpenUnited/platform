from django.conf import settings
from django.utils.module_loading import import_string
from .event_bus import EventBus

def get_event_bus():
    """
    Factory function to get or create an EventBus instance with the configured backend
    """
    backend_path = settings.EVENT_BUS['BACKEND']
    backend_class = import_string(backend_path)
    backend_instance = backend_class()
    
    return EventBus(backend=backend_instance) 