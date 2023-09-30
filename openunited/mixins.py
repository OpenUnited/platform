import uuid
from django.db import models
import json


class TimeStampMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, editable=True)

    class Meta:
        abstract = True


class UUIDMixin(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class AncestryMixin(models.Model):
    class Meta:
        abstract = True

    def ancestry(self):
        lineage = []
        lineage.insert(0, self.name)
        if self.parent is None:
            return json.dumps(lineage)
        else:
            return __class__.s_ancestry(self.parent, lineage)

    @staticmethod
    def s_ancestry(obj, lineage):
        lineage.insert(0, obj.name)
        if obj.parent is None:
            return json.dumps(lineage)
        else:
            return __class__.s_ancestry(obj.parent, lineage)


class VoteMixin(TimeStampMixin, UUIDMixin):
    VOTE_TYPES = ((0, "Up"), (1, "Down"))
    vote_type = models.IntegerField(choices=VOTE_TYPES)
    person = models.ForeignKey("talent.Person", on_delete=models.SET_NULL, null=True)

    class Meta:
        abstract = True


class HTMXInlineFormValidationMixin:
    def _is_htmx_request(self, request):
        htmx_header = request.headers.get("Hx-Request", None)
        return htmx_header == "true"

    def form_valid(self, form):
        if self._is_htmx_request(self.request):
            return self.render_to_response(self.get_context_data(form=form))

        return super().form_valid(form)
