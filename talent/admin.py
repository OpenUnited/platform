from django.contrib import admin

from .models import Person, Status, Feedback, BountyClaim, Expertise, Skill

admin.site.register([Person, Status, Feedback])


@admin.register(BountyClaim)
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


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ["pk", "name", "parent"]


@admin.register(Expertise)
class ExpertiseAdmin(admin.ModelAdmin):
    list_display = ["pk", "name", "skill", "parent"]
