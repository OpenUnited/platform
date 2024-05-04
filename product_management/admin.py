from django.contrib import admin
from product_management import models as product


@admin.register(product.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["slug", "name"]
    search_fields = ["slug", "name"]


@admin.register(product.ProductArea)
class ProductAreaAdmin(admin.ModelAdmin):
    list_display = ["pk", "name", "video_link", "path"]
    search_fields = ["name", "video_link"]


@admin.register(product.ProductAreaAttachment)
class ProductAreaAttachmentAdmin(admin.ModelAdmin):
    list_display = ["pk", "file"]
    search_fields = ["pk", "file"]


@admin.register(product.Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    def capability_name(self, obj):
        return obj.capability.name if obj.capability else "-"

    list_display = ["pk", "title", "status", "priority", "capability_name"]
    search_fields = ["title"]


@admin.register(product.Bounty)
class BountyAdmin(admin.ModelAdmin):
    list_display = ["pk", "title", "status"]
