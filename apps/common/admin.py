from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

# Customize the admin site header and title
admin.site.site_header = 'OpenUnited Admin'
admin.site.site_title = 'OpenUnited Admin Portal'

from apps.capabilities.product_management import models as product_management


@admin.register(product_management.FileAttachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ["pk", "file"]
