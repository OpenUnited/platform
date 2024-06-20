class AttachmentMixin:
    attachment_model = None
    attachment_formset_class = None

    def get_attachment_model(self):
        from apps.product_management.models import FileAttachment

        return FileAttachment

    def get_attachment_formset_class(self):
        from apps.common.forms import AttachmentFormSet

        return AttachmentFormSet

    def get_attachment_queryset(self):
        if self.object:
            return self.object.attachments.all()
        else:
            return self.get_attachment_model().objects.none()

    def get_attachment_formset(self):
        return self.get_attachment_formset_class()(
            self.request.POST or None,
            self.request.FILES or None,
            prefix="attachment_f",
            queryset=self.get_attachment_queryset(),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["attachment_formset"] = self.get_attachment_formset()
        return context

    def form_save(self, form):
        context = self.get_context_data()
        attachment_formset = context["attachment_formset"]

        if attachment_formset.total_form_count() == 0:
            return super().form_valid(form)

        if not form.is_valid() or not attachment_formset.is_valid():
            return self.form_invalid(form)

        response = super().form_valid(form)
        if attachments := attachment_formset.save():
            for attachment in attachments:
                self.object.attachments.add(attachment)
        return response


class PersonSearchMixin:
    def get_template_names(self):
        if self.request.htmx and self.request.GET.get("search"):
            return "partials/dropdown_search.html"
        return super().get_template_names()

    def get_person_model(self):
        from apps.talent.models import Person

        return Person

    def get_person_queryset(self):
        from django.db.models import Q

        if query_parameter := self.request.GET.get("search"):
            query = Q(Q(full_name__icontains=query_parameter) | Q(user__email__icontains=query_parameter))
            return self.get_person_model().objects.filter(query)
        return self.get_person_model().objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_result"] = self.get_person_queryset()
        return context
