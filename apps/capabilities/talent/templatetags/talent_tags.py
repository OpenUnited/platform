from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def range_filter(start, end):
    return range(start, end, -1)

@register.filter
def multiply(value, arg):
    """Multiplies the value by the argument"""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return ''

@register.simple_tag
def skill_filter_tree(children, selected_pk=None, depth=0):
    """
    Renders a hierarchical skill tree as HTML select options
    
    Args:
        children: List of skill nodes
        selected_pk: Currently selected skill ID
        depth: Current depth level for indentation
    """
    html = []
    for node in children:
        # Get id and name, handling both dict and model object cases
        node_id = node.get('id') if isinstance(node, dict) else node.id
        node_name = node.get('name') if isinstance(node, dict) else node.name
        
        # Add the option with proper indentation
        indent = ' ' * (depth * 2)  # 2 spaces per level
        selected = ' selected' if selected_pk and str(node_id) == str(selected_pk) else ''
        html.append(f'<option value="{node_id}"{selected}>{indent}{node_name}</option>')
        
        # Handle children recursively
        node_children = node.get('children') if isinstance(node, dict) else getattr(node, 'children', [])
        if node_children:
            html.extend(skill_filter_tree(node_children, selected_pk, depth + 1))
            
    return mark_safe(''.join(html))

@register.filter
def get_dict_value(dictionary, key):
    return dictionary.get(key) if dictionary else None