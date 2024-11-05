from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def get_ids(queryset):
    return [obj.id for obj in queryset]


@register.filter
def expertise_filter(expertises, skill):
    return [expertise for expertise in expertises if expertise["skill"] == skill]


@register.simple_tag
def skill_filter_tree(skills, skill_id, show_all=False):
    # Your skill filter tree logic here
    return mark_safe(f"<!-- Skill tree for {skill_id} -->")


@register.filter
def get_all(manager):
    return manager.all()
