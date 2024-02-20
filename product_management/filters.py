from django import template, forms
from security.models import ProductRoleAssignment

import django_filters
from product_management.models import Challenge

register = template.Library()


@register.filter
def display_role(role):
    return dict(ProductRoleAssignment.ROLES).get(role, "")


class ChallengeFilter(django_filters.FilterSet):

    class Meta:
        model = Challenge
        fields = [
            "status",
            "priority",
            "reward_type",
        ]
        widget = {
            "status": forms.Select(
                attrs={
                    "class": "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6",
                },
            ),
            "priority": forms.Select(
                attrs={
                    "class": "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6",
                }
            ),
            "reward_type": forms.Select(
                attrs={
                    "class": "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6",
                },
            ),
        }
