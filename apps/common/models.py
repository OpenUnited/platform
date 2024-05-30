from django.db import models


class AttachmentAbstract(models.Model):
    attachments = models.ManyToManyField("product_management.FileAttachment", blank=True)

    class Meta:
        abstract = True
