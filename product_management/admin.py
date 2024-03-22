from django.contrib import admin
from product_management import models as product


@admin.register(product.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["slug", "name"]
    search_fields = ["slug", "name"]


@admin.register(product.Capability)
class CapabilityAdmin(admin.ModelAdmin):
    list_display = ["pk", "name", "video_link", "path"]
    search_fields = ["name", "video_link"]
