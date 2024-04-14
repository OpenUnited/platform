from django.contrib import admin
from product_management import models as product
from talent import models


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
    list_display = ["pk", "challenge", "status"]
    search_fields = ["pk", "status"]


@admin.register(product.BountyAttachment)
class BountyAttachmentAdmin(admin.ModelAdmin):
    list_display = ["pk", "title", "description", "file"]
    search_fields = ["pk", "title", "description"]


@admin.register(models.BountyClaim)
class BountyClaimAdmin(admin.ModelAdmin):
    def bounty_pk(self, obj):
        return obj.bounty.pk or "-"

    list_display = ["pk", "bounty_pk", "status"]
    search_fields = ["pk", "status"]
