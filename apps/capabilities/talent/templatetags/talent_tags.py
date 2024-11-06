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
def skill_filter_tree(skills, skill_id=None, show_all=False):
    """
    Renders a tree of skills as HTML select options
    
    Args:
        skills: QuerySet of Skill objects
        skill_id: ID of currently selected skill (optional)
        show_all: Boolean to show all skills or just active ones
    """
    html = []
    
    for skill in skills:
        selected = ' selected' if skill_id and str(skill.id) == str(skill_id) else ''
        html.append(f'<option value="{skill.id}"{selected}>{skill.name}</option>')
        
    return mark_safe('\n'.join(html))

@register.filter
def get_dict_value(dictionary, key):
    return dictionary.get(key) if dictionary else None