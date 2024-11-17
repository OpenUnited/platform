from django.contrib import admin

from . import models

admin.site.register([models.Feedback])


@admin.register(models.BountyClaim)
class BountyClaimAdmin(admin.ModelAdmin):
    list_display = [
        "pk",
        "bounty",
        "person",
        "expected_finish_date",
        "status",
    ]
    search_fields = [
        "bounty__title",
        "person__user__username",
        "expected_finish_date",
        "status",
    ]


@admin.register(models.Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ["pk", "name", "parent"]


@admin.register(models.Expertise)
class ExpertiseAdmin(admin.ModelAdmin):
    list_display = ["pk", "name", "skill", "fa_icon", "parent"]


@admin.register(models.Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_full_name']
    search_fields = [
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name'
    ]
    ordering = ('user__username',)

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        return queryset, use_distinct


@admin.register(models.PersonSkill)
class PersonSkillAdmin(admin.ModelAdmin):
    list_display = ["pk", "skill", "person"]


@admin.register(models.BountyDeliveryAttempt)
class BountyDeliveryAttemptAdmin(admin.ModelAdmin):
    list_display = ["pk", "kind", "bounty_claim", "person", "is_canceled", "delivery_message"]
    list_filter = ["is_canceled", "kind"]
