class AttachmentMixin:
    attachment_model = None
    attachment_formset_class = None

    def get_attachment_model(self):
        from apps.common.models import FileAttachment

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
            queryset=self.get_attachment_queryset(),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["attachment_formset"] = self.get_attachment_formset()
        return context

    def form_save(self, form):
        context = self.get_context_data()
        attachment_formset = context["attachment_formset"]

        if len(attachment_formset.errors) == 0:
            return super().form_valid(form)

        if not form.is_valid() or not attachment_formset.is_valid():
            return self.form_invalid(form)

        response = super().form_valid(form)
        if attachments := attachment_formset.save():
            for attachment in attachments:
                self.object.attachments.add(attachment)
        return response
