from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.capabilities.talent.models import Person
from apps.capabilities.commerce.models import Organisation

from .models import (
    BlacklistedUsernames, 
    ProductRoleAssignment, 
    SignInAttempt, 
    SignUpRequest, 
    User,
    OrganisationPersonRoleAssignment
)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'get_person_link', 'is_staff')
    readonly_fields = ('get_person_link', 'get_product_roles', 'get_organisation_roles')
    
    def get_person_link(self, obj):
        if hasattr(obj, 'person'):
            url = reverse('admin:talent_person_change', args=[obj.person.id])
            return format_html('<a href="{}">{}</a>', url, obj.person.full_name)
        return "-"
    get_person_link.short_description = 'Person'

    def get_product_roles(self, obj):
        if hasattr(obj, 'person'):
            roles = ProductRoleAssignment.objects.filter(person=obj.person)
            return format_html('<br>'.join(
                f'{role.product.name} - {role.role}' for role in roles
            ))
        return "-"
    get_product_roles.short_description = 'Product Roles'

    def get_organisation_roles(self, obj):
        if hasattr(obj, 'person'):
            roles = OrganisationPersonRoleAssignment.objects.filter(person=obj.person)
            return format_html('<br>'.join(
                f'{role.organisation.name} - {role.role}' for role in roles
            ))
        return "-"
    get_organisation_roles.short_description = 'Organisation Roles'

    fieldsets = (
        (None, {'fields': ('username', 'password', 'get_person_link')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Roles', {'fields': ('get_product_roles', 'get_organisation_roles')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Security', {'fields': ('remaining_budget_for_failed_logins', 'password_reset_required', 'is_test_user')}),
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
    list_filter = ["role"]
    raw_id_fields = ["person", "product"]


@admin.register(OrganisationPersonRoleAssignment)
class OrganisationPersonRoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ('person', 'organisation', 'role')
    raw_id_fields = ('person', 'organisation')
    search_fields = ('person__user__username', 'organisation__name')


admin.site.register(
    [
        SignInAttempt,
        SignUpRequest,
        BlacklistedUsernames,
    ]
)
