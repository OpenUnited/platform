from django.forms import modelformset_factory

from apps.capabilities.product_management import models as product_management

AttachmentFormSet = modelformset_factory(
    product_management.FileAttachment,
    fields=("file",),
    extra=0,
    can_delete=True,
)
