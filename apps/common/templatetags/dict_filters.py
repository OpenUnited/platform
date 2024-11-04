from django import template

register = template.Library()

@register.filter
def get_item(obj, key):
    if hasattr(obj, 'get'):
        return obj.get(key)
    try:
        return obj[key]
    except (KeyError, TypeError, IndexError):
        return None 