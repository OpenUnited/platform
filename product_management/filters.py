from django import template, forms
from django.db import models
from security.models import ProductRoleAssignment

import django_filters
from product_management.models import Challenge, Bounty, Skill, Expertise

register = template.Library()


@register.filter
def display_role(role):
    return dict(ProductRoleAssignment.ROLES).get(role, "")


class ChallengeFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(
        choices=Challenge.CHALLENGE_STATUS,
        initial="Draft",
        empty_label="All Statuses",
        widget=forms.Select(
            attrs={
                "class": "w-full rounded-md border-0 py-1.5 px-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6",
            },
        ),
    )
    priority = django_filters.ChoiceFilter(
        choices=Challenge.CHALLENGE_PRIORITY,
        empty_label="All Priorities",
        widget=forms.Select(
            attrs={
                "class": "w-full rounded-md border-0 py-1.5 px-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6",
            },
        ),
    )
    reward_type = django_filters.ChoiceFilter(
        choices=Challenge.REWARD_TYPE,
        empty_label="All Reward Types",
        widget=forms.Select(
            attrs={
                "class": "w-full rounded-md border-0 py-1.5 px-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6",
            },
        ),
    )

    class Meta:
        model = Challenge
        fields = [
            "status",
            "priority",
            "reward_type",
        ]


class BountyFilter(django_filters.FilterSet):
    class_name = "w-full rounded-md border-0 py-1.5 px-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
    status = django_filters.ChoiceFilter(
        choices=Bounty.BOUNTY_STATUS,
        initial="Draft",
        empty_label="All",
        widget=forms.Select(
            attrs={"class": class_name},
        ),
    )
    skill = django_filters.ModelChoiceFilter(
        queryset=Skill.objects.all(),
        empty_label="All",
        widget=forms.Select(
            attrs={"class": class_name},
        ),
    )
    expertise = django_filters.ModelChoiceFilter(
        queryset=Expertise.objects.all(),
        empty_label="All",
        widget=forms.Select(
            attrs={"class": class_name},
        ),
    )

    class Meta:
        model = Bounty
        fields = [
            "status",
            "skill",
            "expertise",
        ]
