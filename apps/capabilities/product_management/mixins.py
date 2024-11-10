from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from django_lifecycle import BEFORE_CREATE, BEFORE_SAVE, LifecycleModelMixin, hook

from apps.common.mixins import TimeStampMixin, UUIDMixin


class ProductMixin(LifecycleModelMixin, TimeStampMixin, UUIDMixin):
    photo = models.ImageField(upload_to="products/", blank=True, null=True)
    name = models.TextField()
    short_description = models.TextField()
    full_description = models.TextField()
    website = models.CharField(max_length=512, blank=True, null=True)
    detail_url = models.URLField(blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    slug = models.SlugField(unique=True)

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
