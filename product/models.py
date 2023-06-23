from django.db import models

class Product(ProductMixin):
    attachment = models.ManyToManyField(Attachment, related_name="product_attachements", blank=True)
    capability_start = models.ForeignKey(Capability, on_delete=models.CASCADE, null=True, editable=False)
    owner = models.ForeignKey('commercial.ProductOwner', on_delete=models.CASCADE, null=True)

    def get_members_emails(self):
        return self.productperson_set.all().values_list("person__email_address", flat=True)

    def get_members_ids(self):
        return self.productperson_set.all().values_list("person__id", flat=True)

    def is_product_member(self, person):
        return self.productperson_set.filter(person=person).exists()

    def get_product_owner(self):
        product_owner = self.owner
        return product_owner.organisation if product_owner.organisation else product_owner.person.user

    def __str__(self):
        return self.name


@receiver(post_save, sender=Product)
def save_product(sender, instance, created, **kwargs):
    if not created:
        # update challengelisting when product info is updated
        ChallengeListing.objects.filter(product=instance).update(
            product_data=dict(
                name=instance.name,
                slug=instance.slug,
                owner=instance.get_product_owner().username
            )
        )


class Capability(MP_Node):
    name = models.CharField(max_length=255)
    description = models.TextField(max_length=1000, default='')
    video_link = models.CharField(max_length=255, blank=True, null=True)
    comments_start = models.ForeignKey(to='comments.capabilitycomment',
                                       on_delete=models.SET_NULL,
                                       null=True, editable=False)

    class Meta:
        db_table = 'capability'
        verbose_name_plural = 'capabilities'

    def __str__(self):
        return self.name


@receiver(post_save, sender=Capability)
def save_capability(sender, instance, created, **kwargs):
    if not created:
        # update tasklisting when capability info is updated
        ChallengeListing.objects.filter(capability=instance).update(capability_data=to_dict(instance))

class Initiative(TimeStampMixin, UUIDMixin):
    INITIATIVE_STATUS = (
        (1, "Active"),
        (2, "Completed"),
        (3, "Draft"),
        (4, "Cancelled")
    )
    name = models.TextField()
    product = models.ForeignKey(Product, on_delete=models.CASCADE, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    status = models.IntegerField(choices=INITIATIVE_STATUS, default=1)
    video_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name

    def get_available_tasks_count(self):
        return self.task_set.filter(status=Task.TASK_STATUS_AVAILABLE).count()

    def get_completed_task_count(self):
        return self.task_set.filter(status=Task.TASK_STATUS_DONE).count()

    def get_task_tags(self):
        return Tag.objects.filter(task_tags__initiative=self).distinct("id").all()

    @staticmethod
    def get_filtered_data(input_data, filter_data=None, exclude_data=None):
        if filter_data is None:
            filter_data = {}
        if not filter_data:
            filter_data = dict()

        if not input_data:
            input_data = dict()

        statuses = input_data.get("statuses", [])
        tags = input_data.get("tags", [])
        categories = input_data.get("categories", None)

        if statuses:
            filter_data["status__in"] = statuses

        if tags:
            filter_data["task__tag__in"] = tags

        if categories:
            filter_data["task__category__parent__in"] = categories

        queryset = Initiative.objects.filter(**filter_data)
        if exclude_data:
            queryset = queryset.exclude(**exclude_data)

        return queryset.distinct("id").all()


@receiver(post_save, sender=Initiative)
def save_initiative(sender, instance, created, **kwargs):
    if not created:
        # update tasklisting when initiative info is updated
        ChallengeListing.objects.filter(initiative=instance).update(initiative_data=to_dict(instance))


class Attachment(models.Model):
    name = models.CharField(max_length=512)
    path = models.URLField()
    file_type = models.CharField(max_length=5, null=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class CapabilityAttachment(models.Model):
    capability = models.ForeignKey(Capability, on_delete=models.CASCADE)
    attachment = models.ForeignKey(Attachment, on_delete=models.CASCADE)

    class Meta:
        db_table = 'capability_attachment'

class ProductPerson(TimeStampMixin, UUIDMixin):
    PERSON_TYPE_USER = 0
    PERSON_TYPE_PRODUCT_ADMIN = 1
    PERSON_TYPE_PRODUCT_MANAGER = 2
    PERSON_TYPE_CONTRIBUTOR = 3

    PERSON_TYPE = (
        (PERSON_TYPE_USER, "User"),
        (PERSON_TYPE_PRODUCT_ADMIN, "Product Admin"),
        (PERSON_TYPE_PRODUCT_MANAGER, "Product Manager"),
        (PERSON_TYPE_CONTRIBUTOR, "Contributor"),
    )
    product = models.ForeignKey('work.Product', on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    right = models.IntegerField(choices=PERSON_TYPE, default=0)

    def __str__(self):
        return '{} is {} of {}'.format(self.person.user.username, self.get_right_display(), self.product)

