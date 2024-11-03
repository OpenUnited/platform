from django.contrib import admin

from apps.capabilities.product_management import models as product_management


@admin.register(product_management.FileAttachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ["pk", "file"]
