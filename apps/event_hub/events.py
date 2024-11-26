from django.utils.translation import gettext_lazy as _

class EventTypes:
    """Central registry of all application events"""
    
    # Product Events
    PRODUCT_CREATED = 'product.created'
    PRODUCT_UPDATED = 'product.updated'
    PRODUCT_DELETED = 'product.deleted'
    
    # Test Events
    TEST_EVENT = 'test.event'
    TEST_MULTIPLE_LISTENERS = 'test.multiple_listeners'

    # Map events to their display names
    DISPLAY_NAMES = {
        PRODUCT_CREATED: _("Product Created"),
        PRODUCT_UPDATED: _("Product Updated"),
        PRODUCT_DELETED: _("Product Deleted"),
        TEST_EVENT: _("Test Event"),
        TEST_MULTIPLE_LISTENERS: _("Test Multiple Listeners"),
    }


    @classmethod
    def is_notifiable(cls, event_name: str) -> bool:
        """Check if an event should trigger notifications"""
        return event_name in cls.NOTIFIABLE_EVENTS

    @classmethod
    def choices(cls):
        """Return event choices suitable for Django model fields"""
        return [(key, cls.DISPLAY_NAMES[key]) 
                for key in cls.DISPLAY_NAMES.keys()]

    @classmethod
    def validate_event(cls, event_name: str) -> bool:
        """Validate if an event name is registered"""
        return event_name in cls.DISPLAY_NAMES
