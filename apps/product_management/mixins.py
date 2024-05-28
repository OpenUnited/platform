from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from django_lifecycle import BEFORE_CREATE, BEFORE_SAVE, LifecycleModelMixin, hook

from apps.openunited.mixins import TimeStampMixin, UUIDMixin


class ProductMixin(LifecycleModelMixin, TimeStampMixin, UUIDMixin):
    photo = models.ImageField(upload_to="products/", blank=True, null=True)
    name = models.TextField()
    short_description = models.TextField()
    full_description = models.TextField()
    website = models.CharField(max_length=512, blank=True, null=True)
    detail_url = models.URLField(blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    slug = models.SlugField(unique=True)
    is_private = models.BooleanField(default=False)

    def get_initials_of_name(self):
        return "".join([word[0] for word in self.name.split()])

    def get_absolute_url(self):
        return reverse("product_detail", args=(self.slug,))

    @hook(BEFORE_CREATE)
    @hook(BEFORE_SAVE, when="name", has_changed=True)
    def update_slug(self, *args, **kwargs):
        self.slug = slugify(self.name)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class AttachmentMixin:
    attachment_model = None
    attachment_formset_class = None

    def get_attachment_model(self):
        from apps.product_management.models import FileAttachment

        return FileAttachment

    def get_attachment_formset_class(self):
        from apps.product_management.forms import AttachmentFormSet

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
