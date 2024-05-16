from django import template

register = template.Library()


@register.filter
def get_ids(queryset):
    return [obj.id for obj in queryset]


@register.filter
def expertise_filter(expertises, skill):
    return [
        expertise for expertise in expertises if expertise["skill"] == skill
    ]
