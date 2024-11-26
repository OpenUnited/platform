from django.conf import settings
from django.utils.module_loading import import_string
from .event_bus import EventBus

_event_bus_instance = None  # Module-level singleton instance

def get_event_bus():
    """
    Factory function to get or create an EventBus instance with the configured backend
    """
    global _event_bus_instance

    if _event_bus_instance is None:
        backend_path = settings.EVENT_BUS['BACKEND']
        backend_class = import_string(backend_path)
        backend_instance = backend_class()
        
        _event_bus_instance = EventBus(backend=backend_instance)

    return _event_bus_instance 