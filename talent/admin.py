from django.contrib import admin

from .models import Talent


@admin.register(Talent)
class TalentAdmin(admin.ModelAdmin):
    readonly_fields = ("date_joined",)
    fieldsets = (
        (
            "General Information",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "username",
                    "email",
                    "password",
                )
            },
        ),
        (
            "Talent Details",
            {
                "fields": (
                    "headline",
                    "overview",
                    "photo",
                    "send_me_bounties",
                    "date_joined",
                ),
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_test_user",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )
