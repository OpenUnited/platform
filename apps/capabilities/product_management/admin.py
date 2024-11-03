from django.contrib import admin

from apps.capabilities.product_management import models as product


@admin.register(product.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["slug", "name", "visibility", "owner_type", "owner"]
    list_filter = ["visibility"]
    search_fields = ["slug", "name", "organisation__name", "person__name"]
    raw_id_fields = ["organisation", "person"]


@admin.register(product.Initiative)
class InitiativeAdmin(admin.ModelAdmin):
    list_display = ["product", "status"]
    search_fields = ["product__name", "status"]


@admin.register(product.ProductTree)
class ProductTreeAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at"]
    search_fields = ["name"]


@admin.register(product.ProductArea)
class ProductAreaAdmin(admin.ModelAdmin):
    list_display = ["pk", "name", "product_tree", "video_link", "path"]
    search_fields = ["name", "video_link"]
    filter_horizontal = ("attachments",)


@admin.register(product.Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    def product_area_name(self, obj):
        return obj.product_area.name if obj.product_area else "-"

    list_display = ["pk", "title", "status", "priority", "product_area_name"]
    search_fields = ["title"]
    filter_horizontal = ["attachments"]


@admin.register(product.Bounty)
class BountyAdmin(admin.ModelAdmin):
    list_display = ["pk", "title", "status"]
    list_filter = ["status"]
    search_fields = ["title"]
    filter_horizontal = ["expertise", "attachments"]
