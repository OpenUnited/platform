from django.contrib import admin
from django.contrib.auth import admin as auth_admin

from .models import (
    BlacklistedUsernames, 
    ProductRoleAssignment, 
    SignInAttempt, 
    SignUpRequest, 
    User,
    OrganisationPersonRoleAssignment
)


@admin.register(User)
class UserAdminAdmin(auth_admin.UserAdmin):
    list_display = ["pk", "first_name", "last_name", "username"]
    search_fields = ["pk", "first_name", "last_name", "username"]


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
    list_filter = ["role"]
    raw_id_fields = ["person", "product"]


@admin.register(OrganisationPersonRoleAssignment)
class OrganisationPersonRoleAssignmentAdmin(admin.ModelAdmin):
    def organisation_name(self, obj):
        return obj.organisation.name

    def person_name(self, obj):
        return obj.person.user

    list_display = ["pk", "organisation_name", "person_name", "role"]
    search_fields = [
        "person__user__username",
        "person__user__email",
        "organisation__name",
    ]
    list_filter = ["role"]
    raw_id_fields = ["person", "organisation"]


admin.site.register(
    [
        SignInAttempt,
        SignUpRequest,
        BlacklistedUsernames,
    ]
)
