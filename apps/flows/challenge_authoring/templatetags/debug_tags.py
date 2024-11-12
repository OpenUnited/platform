from django import template
import inspect

register = template.Library()

@register.simple_tag(takes_context=True)
def debug_template_location(context):
    template = context.template.name if hasattr(context, 'template') else 'Unknown'
    frame = inspect.currentframe()
    caller = inspect.getouterframes(frame)[1]
    return f"<!-- Template: {template} loaded from {caller.filename}:{caller.lineno} -->" 