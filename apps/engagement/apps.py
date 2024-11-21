from django.apps import AppConfig


class EngagementConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.engagement"

    def ready(self):
        from apps.event_hub.services.factory import get_event_bus
        from .events import handle_product_created

        event_bus = get_event_bus()
        event_bus.register_listener('product.created', handle_product_created)
