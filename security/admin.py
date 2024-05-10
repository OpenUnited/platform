from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from .models import (
    User,
    SignInAttempt,
    SignUpRequest,
    ProductRoleAssignment,
    BlacklistedUsernames,
)

admin.site.register(
    [
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


@admin.register(User)
class UserAdminAdmin(auth_admin.UserAdmin):
    list_display = ["pk", "first_name", "last_name", "username"]
    search_fields = ["pk", "first_name", "last_name", "username"]
