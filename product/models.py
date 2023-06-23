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
