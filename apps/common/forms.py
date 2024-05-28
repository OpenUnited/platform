from django.forms import modelformset_factory

from apps.common import models as common

AttachmentFormSet = modelformset_factory(
    common.FileAttachment,
    fields=("file",),
    extra=0,
    can_delete=True,
)
