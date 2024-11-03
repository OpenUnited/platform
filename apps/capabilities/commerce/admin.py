from django.contrib import admin
from django.utils.html import format_html
from .models import Organisation, OrganisationAccount

@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ('name', 'username', 'display_photo', 'created_at', 'updated_at')
    search_fields = ('name', 'username')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    list_filter = ('created_at', 'updated_at')

    def display_photo(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="50" height="50" />', obj.photo.url)
        return "No photo"
    display_photo.short_description = 'Photo'

@admin.register(OrganisationAccount)
class OrganisationAccountAdmin(admin.ModelAdmin):
    list_display = ('organisation', 'liquid_points_balance', 'nonliquid_points_balance')
    search_fields = ('organisation__name',)
    list_filter = ('organisation',)
    raw_id_fields = ('organisation',)

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return ('liquid_points_balance', 'nonliquid_points_balance')
        return ()
