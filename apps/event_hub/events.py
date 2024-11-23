from django.utils.translation import gettext_lazy as _

class EventTypes:
    """Central registry of all application events"""
    
    # Product Events
    PRODUCT_CREATED = 'product.created'
    PRODUCT_UPDATED = 'product.updated'
    PRODUCT_DELETED = 'product.deleted'

    # Map events to their display names
    DISPLAY_NAMES = {
        PRODUCT_CREATED: _("Product Created"),
        PRODUCT_UPDATED: _("Product Updated"),
        PRODUCT_DELETED: _("Product Deleted"),
    }

    @classmethod
    def choices(cls):
        """Return event choices suitable for Django model fields"""
        return [(key, cls.DISPLAY_NAMES[key]) 
                for key in cls.DISPLAY_NAMES.keys()]

    @classmethod
    def validate_event(cls, event_name: str) -> bool:
        """Validate if an event name is registered"""
        return event_name in cls.DISPLAY_NAMES
