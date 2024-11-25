from django.apps import AppConfig
from apps.event_hub.events import EventTypes


class EngagementConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.engagement"

    def ready(self):
        from apps.event_hub.services.factory import get_event_bus
        from .events import (
            handle_product_created,
            handle_product_updated,
            # Add other handlers as needed
        )

        event_bus = get_event_bus()
        
        # Register all event handlers
        event_bus.register_listener(EventTypes.PRODUCT_CREATED, handle_product_created)
        event_bus.register_listener(EventTypes.PRODUCT_UPDATED, handle_product_updated)
        # Add other event registrations as needed
