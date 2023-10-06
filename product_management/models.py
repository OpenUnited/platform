from django.conf import settings
from django.db import models
from django.urls import reverse
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from model_utils import FieldTracker
from django.utils.text import slugify
from treebeard.mp_tree import MP_Node

from openunited.mixins import TimeStampMixin, UUIDMixin
from openunited.settings.base import MEDIA_URL, PERSON_PHOTO_UPLOAD_TO
from product_management.mixins import ProductMixin
from talent.models import Person, Skill, Expertise


class Tag(TimeStampMixin):
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name


# ProductTree is made up from Capabilities
class Capability(MP_Node):
    name = models.CharField(max_length=255)
    description = models.TextField(max_length=1000, default="")
    video_link = models.CharField(max_length=255, blank=True, null=True)
    comments_start = models.ForeignKey(
        to="talent.capabilitycomment",
        on_delete=models.SET_NULL,
        null=True,
        editable=False,
    )

    class Meta:
        db_table = "capability"
        verbose_name_plural = "capabilities"

    def __str__(self):
        return self.name


class Attachment(models.Model):
    name = models.CharField(max_length=512)
    path = models.URLField()
    file_type = models.CharField(max_length=5, null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class CapabilityAttachment(models.Model):
    capability = models.ForeignKey(Capability, on_delete=models.CASCADE)
    attachment = models.ForeignKey(Attachment, on_delete=models.CASCADE)

    class Meta:
        db_table = "capability_attachment"


class Product(ProductMixin):
    attachment = models.ManyToManyField(
        Attachment, related_name="product_attachments", blank=True
    )
    capability_start = models.ForeignKey(
        Capability, on_delete=models.CASCADE, null=True, editable=False
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    def make_private(self):
        self.is_private = True
        self.save()

    def make_public(self):
        self.is_private = False
        self.save()

    # TODO: this method also exists in Person model. Move it in a mixin and
    # separate requires_upload variable from this method
    def get_photo_url(self) -> [str, bool]:
        image_url = MEDIA_URL + PERSON_PHOTO_UPLOAD_TO + "profile-empty.png"
        requires_upload = True

        if self.photo:
            image_url = self.photo.url
            requires_upload = False

        return image_url, requires_upload

    @staticmethod
    def check_slug_from_name(product_name: str) -> str | None:
        """Checks if the given product name already exists. If so, it returns an error message."""
        slug = slugify(product_name)

        if Product.objects.filter(slug=slug):
            return f"The name {product_name} is not available currently. Please pick something different."

    def save(self, *args, **kwargs):
        # We show the preview of the video in ProductListing. Therefore, we have to
        # convert the given URL to an embed
        from .services import ProductService

        self.video_url = ProductService.convert_youtube_link_to_embed(self.video_url)
        super(Product, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


class Initiative(TimeStampMixin, UUIDMixin):
    INITIATIVE_STATUS = (
        (1, "Active"),
        (2, "Completed"),
        (3, "Draft"),
        (4, "Cancelled"),
    )
    name = models.TextField()
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, blank=True, null=True
    )
    description = models.TextField(blank=True, null=True)
    status = models.IntegerField(choices=INITIATIVE_STATUS, default=1)
    video_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # TODO: move the below method to a utility class
        from .services import ProductService

        self.video_url = ProductService.convert_youtube_link_to_embed(self.video_url)
        super(Initiative, self).save(*args, **kwargs)

    def get_available_challenges_count(self):
        return self.challenge_set.filter(
            status=Challenge.CHALLENGE_STATUS_AVAILABLE
        ).count()

    def get_completed_challenges_count(self):
        return self.challenge_set.filter(status=Challenge.CHALLENGE_STATUS_DONE).count()

    def get_challenge_tags(self):
        return Challenge.objects.filter(task_tags__initiative=self).distinct("id").all()

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
            filter_data["challenge__tag__in"] = tags

        if categories:
            filter_data["challenge__category__parent__in"] = categories

        queryset = Initiative.objects.filter(**filter_data)
        if exclude_data:
            queryset = queryset.exclude(**exclude_data)

        return queryset.distinct("id").all()


class Challenge(TimeStampMixin, UUIDMixin):
    CHALLENGE_STATUS_DRAFT = 0
    CHALLENGE_STATUS_BLOCKED = 1
    CHALLENGE_STATUS_AVAILABLE = 2
    CHALLENGE_STATUS_CLAIMED = 3
    CHALLENGE_STATUS_DONE = 4
    CHALLENGE_STATUS_IN_REVIEW = 5

    CHALLENGE_STATUS = (
        (CHALLENGE_STATUS_DRAFT, "Draft"),
        (CHALLENGE_STATUS_BLOCKED, "Blocked"),
        (CHALLENGE_STATUS_AVAILABLE, "Available"),
        (CHALLENGE_STATUS_CLAIMED, "Claimed"),
        (CHALLENGE_STATUS_DONE, "Done"),
        (CHALLENGE_STATUS_IN_REVIEW, "In review"),
    )
    CHALLENGE_PRIORITY = ((0, "High"), (1, "Medium"), (2, "Low"))

    REWARD_TYPE = (
        (0, "Liquid Points"),
        (1, "Non-liquid Points"),
    )

    initiative = models.ForeignKey(
        Initiative, on_delete=models.SET_NULL, blank=True, null=True
    )
    capability = models.ForeignKey(
        Capability, on_delete=models.SET_NULL, blank=True, null=True
    )
    title = models.TextField()
    description = models.TextField()
    short_description = models.TextField(max_length=256)
    status = models.IntegerField(choices=CHALLENGE_STATUS, default=0)
    attachment = models.ManyToManyField(
        Attachment, related_name="challenge_attachements", blank=True
    )
    tag = models.ManyToManyField(Tag, related_name="challenge_tags", blank=True)
    blocked = models.BooleanField(default=False)
    featured = models.BooleanField(default=False)
    priority = models.IntegerField(choices=CHALLENGE_PRIORITY, default=1)
    published_id = models.IntegerField(default=0, blank=True, editable=False)
    auto_approve_task_claims = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        "talent.Person",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="created_by",
    )
    updated_by = models.ForeignKey(
        "talent.Person",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="updated_by",
    )
    tracker = FieldTracker()
    comments_start = models.ForeignKey(
        to="talent.challengecomment",
        on_delete=models.SET_NULL,
        null=True,
        editable=False,
    )
    reviewer = models.ForeignKey("talent.Person", on_delete=models.SET_NULL, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    video_url = models.URLField(blank=True, null=True)
    contribution_guide = models.ForeignKey(
        "ContributorGuide",
        null=True,
        default=None,
        blank=True,
        on_delete=models.SET_NULL,
    )
    reward_type = models.IntegerField(choices=REWARD_TYPE, default=1)

    class Meta:
        verbose_name_plural = "Challenges"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse(
            "challenge_detail",
            kwargs={"product_slug": self.product.slug, "challenge_id": self.pk},
        )

    def can_delete_challenge(self, person):
        from security.models import ProductRoleAssignment

        product = self.product
        # That should not happen because every challenge should have a product.
        # We could remove null=True statement from the product field and this
        # if statement to prevent having challenges without a product.
        if product is None:
            return False

        product_role_assignment = ProductRoleAssignment.objects.filter(
            person=person, product=product
        ).first()

        if product_role_assignment is None:
            return False

        if product_role_assignment.role == ProductRoleAssignment.CONTRIBUTOR:
            return False

        return True

    def has_bounty(self):
        return self.bounty_set.count() > 0

    def get_bounty_points(self):
        total = 0
        queryset = self.bounty_set.all()
        for elem in queryset:
            total += elem.points

        return total

    @staticmethod
    def get_filtered_data(input_data, filter_data=None, exclude_data=None):
        if not filter_data:
            filter_data = {}

        if not input_data:
            input_data = {}

        sorted_by = input_data.get("sorted_by", "title")
        statuses = input_data.get("statuses", [])
        tags = input_data.get("tags", [])
        priority = input_data.get("priority", [])
        assignee = input_data.get("assignee", [])
        task_creator = input_data.get("task_creator", [])
        skills = input_data.get("skils", [])

        if statuses:
            filter_data["status__in"] = statuses

        if tags:
            filter_data["tag__in"] = tags

        if priority:
            filter_data["priority__in"] = priority

        if task_creator:
            filter_data["created_by__in"] = task_creator

        if assignee:
            filter_data["bountyclaim__kind__in"] = [0, 1]
            filter_data["bountyclaim__person_id__in"] = assignee

        if skills:
            filter_data["skill__parent__in"] = skills

        queryset = Challenge.objects.filter(**filter_data)
        if exclude_data:
            queryset = queryset.exclude(**exclude_data)

        return queryset.order_by(sorted_by).all()

    def get_challenge_link(self, show_domain_name=True):
        try:
            product = self.productchallenge_set.first().product
            product_owner = product.get_product_owner()
            domain_name = settings.FRONT_END_SERVER if show_domain_name else ""
            return f"{domain_name}/{product_owner.username}/{product.slug}/challenges/{self.published_id}"
        except ProductChallenge.DoesNotExist:
            return None


class Bounty(TimeStampMixin):
    BOUNTY_STATUS_DRAFT = 0
    BOUNTY_STATUS_BLOCKED = 1
    BOUNTY_STATUS_AVAILABLE = 2
    BOUNTY_STATUS_CLAIMED = 3
    BOUNTY_STATUS_DONE = 4
    BOUNTY_STATUS_IN_REVIEW = 5

    BOUNTY_STATUS = (
        (BOUNTY_STATUS_DRAFT, "Draft"),
        (BOUNTY_STATUS_BLOCKED, "Blocked"),
        (BOUNTY_STATUS_AVAILABLE, "Available"),
        (BOUNTY_STATUS_CLAIMED, "Claimed"),
        (BOUNTY_STATUS_DONE, "Done"),
        (BOUNTY_STATUS_IN_REVIEW, "In review"),
    )

    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE)
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name="bounty_skill",
        blank=True,
        null=True,
        default=None,
    )
    expertise = models.ManyToManyField(Expertise, related_name="bounty_expertise")
    points = models.IntegerField()
    status = models.IntegerField(choices=BOUNTY_STATUS, default=BOUNTY_STATUS_AVAILABLE)
    is_active = models.BooleanField(default=True)

    def get_expertise_as_str(self):
        return ", ".join([exp.name.title() for exp in self.expertise.all()])

    def __str__(self):
        return f"{self.challenge.title} - {self.skill} - {self.get_expertise_as_str()} - {self.points} - {self.get_status_display()}"


class ChallengeDependency(models.Model):
    preceding_challenge = models.ForeignKey(to=Challenge, on_delete=models.CASCADE)
    subsequent_challenge = models.ForeignKey(
        to=Challenge, on_delete=models.CASCADE, related_name="Challenge"
    )

    class Meta:
        db_table = "product_management_challenge_dependencies"


class ProductChallenge(TimeStampMixin, UUIDMixin):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE)


@receiver(post_save, sender=ProductChallenge)
def save_product_task(sender, instance, created, **kwargs):
    if created:
        challenge = instance.challenge
        last_product_challenge = (
            Challenge.objects.filter(productchallenge__product=instance.product)
            .order_by("-published_id")
            .first()
        )
        challenge.published_id = (
            last_product_challenge.published_id + 1 if last_product_challenge else 1
        )
        challenge.save()


class ContributorAgreement(models.Model):
    product = models.ForeignKey(
        to=Product,
        on_delete=models.CASCADE,
        related_name="product_contributor_agreement",
    )
    agreement_content = models.TextField()

    class Meta:
        db_table = "contribution_management_contributor_agreement"


class ContributorAgreementAcceptance(models.Model):
    agreement = models.ForeignKey(to=ContributorAgreement, on_delete=models.CASCADE)
    person = models.ForeignKey(
        to="talent.Person",
        on_delete=models.CASCADE,
        related_name="person_contributor_agreement_acceptance",
    )
    accepted_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = "contribution_management_contributor_agreement_acceptance"


class ContributorGuide(models.Model):
    product = models.ForeignKey(
        to=Product, on_delete=models.CASCADE, related_name="product_contributor_guide"
    )
    title = models.CharField(max_length=60, unique=True)
    description = models.TextField(null=True, blank=True)
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name="category_contributor_guide",
        blank=True,
        null=True,
        default=None,
    )

    def __str__(self):
        return self.title


class Idea(TimeStampMixin):
    title = models.CharField(max_length=256)
    description = models.TextField()
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    vote_count = models.PositiveSmallIntegerField(default=0)

    def get_absolute_url(self):
        return reverse("add_product_idea", kwargs={"pk": self.pk})

    def __str__(self):
        return f"{self.person} - {self.title}"
