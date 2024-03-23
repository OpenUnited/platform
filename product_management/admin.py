from django.contrib import admin
from product_management import models as product


@admin.register(product.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["slug", "name"]
    search_fields = ["slug", "name"]


@admin.register(product.ProductArea)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["pk", "name", "video_link", "path"]
    search_fields = ["name", "video_link"]


@admin.register(product.Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    def capability_name(self, obj):
        if obj.capability:
            return obj.capability.name

        return "-"

    list_display = ["pk", "title", "status", "priority", "capability_name"]
    search_fields = ["title"]
