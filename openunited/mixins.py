import uuid
from django.db import models


class TimeStampMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, editable=True)

    class Meta:
        abstract = True


class UUIDMixin(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class VoteMixin(TimeStampMixin, UUIDMixin):
    VOTE_TYPES = (
        (0, "Up"),
        (1, "Down")
    )
    vote_type = models.IntegerField(choices=VOTE_TYPES)
    person = models.ForeignKey("talent.Person", on_delete=models.SET_NULL, null=True)

    class Meta:
        abstract = True
