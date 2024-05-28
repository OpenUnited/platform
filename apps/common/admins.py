from django.contrib import admin

from apps.common import models as common


@admin.register(common.FileAttachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ["pk", "file"]
