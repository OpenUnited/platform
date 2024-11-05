from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Template filter to get an item from a dictionary using a variable key
    Usage: {{ my_dict|get_item:my_key }}
    """
    return dictionary.get(key) 