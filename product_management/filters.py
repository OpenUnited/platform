from django import template
from security.models import ProductRoleAssignment

register = template.Library()


@register.filter
def display_role(role):
    return dict(ProductRoleAssignment.ROLES).get(role, "")
