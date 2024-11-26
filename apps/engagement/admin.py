from django.contrib import admin
from .models import (
    NotifiableEvent,
    NotificationPreference,
    AppNotificationTemplate,
    AppNotification,
    EmailNotificationTemplate,
    EmailNotification
)

@admin.register(NotifiableEvent)
class NotifiableEventAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'person', 'created_at', 'delete_at')
    list_filter = ('event_type', 'created_at')
    search_fields = ('person__email', 'person__first_name', 'person__last_name')
    readonly_fields = ('created_at',)

@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('person', 'product_notifications')
    search_fields = ('person__email', 'person__first_name', 'person__last_name')
    readonly_fields = ('created_at',)

@admin.register(AppNotificationTemplate)
class AppNotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'title')
    search_fields = ('event_type', 'title', 'template')

@admin.register(AppNotification)
class AppNotificationAdmin(admin.ModelAdmin):
    list_display = ('person', 'title', 'is_read', 'read_at', 'created_at')
    list_filter = ('is_read', 'created_at', 'read_at')
    search_fields = ('person__email', 'title', 'message')
    readonly_fields = ('created_at',)

@admin.register(EmailNotificationTemplate)
class EmailNotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'title')
    search_fields = ('event_type', 'title', 'template')

@admin.register(EmailNotification)
class EmailNotificationAdmin(admin.ModelAdmin):
    list_display = ('person', 'title', 'sent_at', 'delete_at')
    list_filter = ('sent_at',)
    search_fields = ('person__email', 'title', 'body')
    readonly_fields = ('created_at',)
