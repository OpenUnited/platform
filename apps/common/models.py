from django.db import models


class FileAttachment(models.Model):
    file = models.FileField(upload_to="attachments")

    def __str__(self):
        return f"{self.file.name}"


class AttachmentAbstract(models.Model):
    attachments = models.ManyToManyField("common.FileAttachment", blank=True)

    class Meta:
        abstract = True
