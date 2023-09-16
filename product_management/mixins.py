from django_lifecycle import LifecycleModelMixin, hook, BEFORE_CREATE, BEFORE_SAVE
from django.db import models
from openunited.mixins import TimeStampMixin, UUIDMixin
from django.utils.text import slugify


class ProductMixin(LifecycleModelMixin, TimeStampMixin, UUIDMixin):
    photo = models.CharField(blank=True, null=True, default=None, max_length=1024)
    name = models.TextField()
    short_description = models.TextField()
    full_description = models.TextField(blank=True, null=True)
    website = models.CharField(max_length=512, blank=True, null=True)
    detail_url = models.URLField(blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    slug = models.SlugField(unique=True)
    is_private = models.BooleanField(default=False)

    @hook(BEFORE_CREATE)
    @hook(BEFORE_SAVE, when="name", has_changed=True)
    def update_slug(self, *args, **kwargs):
        self.slug = slugify(self.name)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name
