from django import template
import os

register = template.Library()

@register.filter
def basename(value):
    """Returns the filename from a path."""
    return os.path.basename(value) 