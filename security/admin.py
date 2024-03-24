from django.contrib import admin

from .models import (
    User,
    SignInAttempt,
    SignUpRequest,
    ProductRoleAssignment,
    BlacklistedUsernames,
)

admin.site.register(
    [
        User,
        SignInAttempt,
        SignUpRequest,
        BlacklistedUsernames,
    ]
)


@admin.register(ProductRoleAssignment)
class ProductRoleAssignmentAdmin(admin.ModelAdmin):
    def product_name(self, obj):
        return obj.product.name

    def person_name(self, obj):
        return obj.person.user

    list_display = ["pk", "product_name", "person_name", "role"]
    search_fields = [
        "person__user__username",
        "person__user__email",
        "product__name",
    ]
