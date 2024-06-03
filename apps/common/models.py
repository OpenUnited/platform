import uuid

from django.db import models


class AttachmentAbstract(models.Model):
    attachments = models.ManyToManyField("product_management.FileAttachment", blank=True)

    class Meta:
        abstract = True


class AbstractModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, editable=True)

    class Meta:
        abstract = True
        ordering = ("-created_at",)
