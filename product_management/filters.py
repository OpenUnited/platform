from django import template
from security.models import ProductPerson

register = template.Library()


@register.filter
def display_role(role):
    return dict(ProductPerson.ROLES).get(role, "")
