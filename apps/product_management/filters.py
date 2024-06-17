from django import forms, template

import django_filters

from apps.product_management.models import Challenge

register = template.Library()


class ChallengeFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(
        choices=Challenge.ChallengeStatus.choices,
        initial="Draft",
        empty_label="All Statuses",
        widget=forms.Select(
            attrs={
                "class": (
                    "w-full rounded-md border-0 py-1.5 px-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300"
                    " focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
                ),
            },
        ),
    )
    priority = django_filters.ChoiceFilter(
        choices=Challenge.ChallengePriority.choices,
        empty_label="All Priorities",
        widget=forms.Select(
            attrs={
                "class": (
                    "w-full rounded-md border-0 py-1.5 px-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300"
                    " focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
                ),
            },
        ),
    )
    reward_type = django_filters.ChoiceFilter(
        choices=Challenge.RewardType.choices,
        empty_label="All Reward Types",
        widget=forms.Select(
            attrs={
                "class": (
                    "w-full rounded-md border-0 py-1.5 px-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300"
                    " focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm sm:leading-6"
                ),
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
