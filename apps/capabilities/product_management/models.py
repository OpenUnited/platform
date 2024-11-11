from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.text import slugify
from django.core.exceptions import ValidationError

from model_utils import FieldTracker
from treebeard.mp_tree import MP_Node

from apps.common import models as common
from apps.common.mixins import TimeStampMixin, UUIDMixin
from apps.capabilities.product_management.mixins import ProductMixin

import uuid


class FileAttachment(models.Model):
    file = models.FileField(upload_to="attachments")

    def __str__(self):
        return f"{self.file.name}"


class ProductTree(common.AbstractModel):
    name = models.CharField(max_length=255, unique=True)
    session_id = models.CharField(max_length=255, blank=True, null=True)
    product = models.ForeignKey(
        "product_management.Product",
        related_name="product_trees",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.name


class ProductArea(MP_Node, common.AbstractModel, common.AttachmentAbstract):
    id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")
    name = models.CharField(max_length=255)
    description = models.TextField(max_length=1000, blank=True, null=True, default="")
    video_link = models.URLField(max_length=255, blank=True, null=True)
    video_name = models.CharField(max_length=255, blank=True, null=True)
    video_duration = models.CharField(max_length=255, blank=True, null=True)
    product_tree = models.ForeignKey(
        "product_management.ProductTree",
        blank=True,
        null=True,
        related_name="product_areas",
        on_delete=models.SET_NULL,
    )
    comments_start = models.ForeignKey(
        to="talent.capabilitycomment",
        on_delete=models.SET_NULL,
        null=True,
        editable=False,
    )

    def __str__(self):
        return self.name


class Product(TimeStampMixin, UUIDMixin, common.AttachmentAbstract):
    """
    Represents a product that can be owned by either a Person or an Organisation, but not both.
    This is enforced through a database constraint 'product_single_owner' which ensures
    exactly one of person or organisation is set.

    Products have three visibility levels:
    - GLOBAL: Visible to all users
    - ORG_ONLY: Only visible to members of the owning organisation
    - RESTRICTED: Only visible to organisation members with explicit ProductRoleAssignment

    Attributes:
        person (ForeignKey): Individual owner, mutually exclusive with organisation
        organisation (ForeignKey): Organisational owner, mutually exclusive with person
        visibility (CharField): Controls product visibility using Visibility choices
    """
    class Visibility(models.TextChoices):
        GLOBAL = "GLOBAL", "Global"
        ORG_ONLY = "ORG_ONLY", "Organisation Only"
        RESTRICTED = "RESTRICTED", "Restricted"

    visibility = models.CharField(
        max_length=10,
        choices=Visibility.choices,
        default=Visibility.ORG_ONLY
    )

    person = models.ForeignKey(
        "talent.Person", 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='owned_products'
    )
    organisation = models.ForeignKey(
        "commerce.Organisation", 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='owned_products'
    )


    name = models.CharField(max_length=255)
    short_description = models.TextField(max_length=256, blank=True, null=True)
    full_description = models.TextField(blank=True, null=True)
    website = models.URLField(max_length=255, blank=True, null=True)
    detail_url = models.URLField(max_length=255, blank=True, null=True)
    video_url = models.URLField(max_length=255, blank=True, null=True)
    slug = models.SlugField(max_length=255, unique=True)
    photo = models.ImageField(upload_to='products', blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['organisation']),
            models.Index(fields=['person']),
        ]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(person__isnull=True, organisation__isnull=False) |
                    models.Q(person__isnull=False, organisation__isnull=True)
                ),
                name='product_single_owner'
            )
        ]

    @property
    def owner(self):
        """Returns the owner (either Organisation or Person) of the product"""
        return self.organisation or self.person

    @property
    def owner_type(self) -> str:
        """Returns 'organisation' or 'person' depending on owner type"""
        return 'organisation' if self.organisation else 'person'

    def is_owned_by_organisation(self) -> bool:
        """Check if product is owned by an organisation"""
        return self.organisation is not None

    def is_owned_by_person(self) -> bool:
        """Check if product is owned by an individual person"""
        return self.person is not None

    def can_user_manage(self, user) -> bool:
        """Check if a user can manage this product"""
        from apps.capabilities.security.services import RoleService
        
        if not user or not user.is_authenticated:
            return False

        if self.is_owned_by_person() and self.person_id == user.person.id:
            return True

        if self.is_owned_by_organisation():
            return RoleService.is_organisation_manager(user.person, self.organisation)

        return False

    def get_photo_url(self):
        """Get the product photo URL or default image"""
        return self.photo.url if self.photo else f"{settings.STATIC_URL}images/product-empty.png"

    # Validates owner exclusivity (person XOR org) and visibility rules for person-owned products
    def clean(self):
        """Validate that only one owner type is set"""
        if self.person and self.organisation:
            raise ValidationError("Product cannot have both person and organisation as owner")
        if not self.person and not self.organisation:
            raise ValidationError("Product must have either person or organisation as owner")
        if self.is_owned_by_person() and self.visibility != self.Visibility.GLOBAL:
            raise ValidationError({
                'visibility': 'Person-owned products can only have GLOBAL visibility'
            })

    @classmethod
    def check_slug_from_name(cls, name):
        """
        Check if a slug generated from the given name would be unique
        
        Args:
            name: The product name to check
            
        Returns:
            bool: True if slug would be unique, False otherwise
        """
        potential_slug = slugify(name)
        return not cls.objects.filter(slug=potential_slug).exists()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("product_management:product-summary", kwargs={"product_slug": self.slug})


class Initiative(TimeStampMixin, UUIDMixin):
    class InitiativeStatus(models.TextChoices):
        DRAFT = "Draft"
        ACTIVE = "Active"
        COMPLETED = "Completed"
        CANCELLED = "Cancelled"

    name = models.TextField()
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='initiatives'
    )
    description = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=255,
        choices=InitiativeStatus.choices,
        default=InitiativeStatus.ACTIVE,
    )
    video_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def get_available_challenges_count(self):
        return self.challenge_set.filter(status=Challenge.ChallengeStatus.ACTIVE).count()

    def get_completed_challenges_count(self):
        return self.challenge_set.filter(status=Challenge.ChallengeStatus.COMPLETED).count()

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


class Challenge(TimeStampMixin, UUIDMixin, common.AttachmentAbstract):
    class ChallengeStatus(models.TextChoices):
        DRAFT = "Draft"
        BLOCKED = "Blocked"
        ACTIVE = "Active"
        COMPLETED = "Completed"
        CANCELLED = "Cancelled"

    class RewardType(models.TextChoices):
        LIQUID_POINTS = "Liquid Points"
        NON_LIQUID_POINTS = "Non-liquid Points"

    class ChallengePriority(models.TextChoices):
        HIGH = "High"
        MEDIUM = "Medium"
        LOW = "Low"

    initiative = models.ForeignKey(Initiative, on_delete=models.SET_NULL, blank=True, null=True)
    product_area = models.ForeignKey(ProductArea, on_delete=models.SET_NULL, blank=True, null=True)
    title = models.TextField()
    description = models.TextField()
    short_description = models.TextField(max_length=256)
    status = models.CharField(
        max_length=255,
        choices=ChallengeStatus.choices,
        default=ChallengeStatus.DRAFT,
    )
    blocked = models.BooleanField(default=False)
    featured = models.BooleanField(default=False)
    priority = models.CharField(
        max_length=50,
        choices=ChallengePriority.choices,
        default=ChallengePriority.HIGH,
    )
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
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    video_url = models.URLField(blank=True, null=True)
    contribution_guide = models.ForeignKey(
        "ContributorGuide",
        null=True,
        default=None,
        blank=True,
        on_delete=models.SET_NULL,
    )
    reward_type = models.CharField(
        max_length=50,
        choices=RewardType.choices,
        default=RewardType.NON_LIQUID_POINTS,
    )

    class Meta:
        verbose_name_plural = "Challenges"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse(
            'product_management:challenge-detail',
            kwargs={
                'product_slug': self.product.slug,
                'pk': self.id
            }
        )

    def can_delete_challenge(self, person):
        from apps.capabilities.security.models import ProductRoleAssignment

        product = self.product
        # That should not happen because every challenge should have a product.
        # We could remove null=True statement from the product field and this
        # if statement to prevent having challenges without a product.
        if product is None:
            return False

        try:
            product_role_assignment = ProductRoleAssignment.objects.get(person=person, product=product)

            if product_role_assignment.role == ProductRoleAssignment.ProductRoles.CONTRIBUTOR:
                return False

        except ProductRoleAssignment.DoesNotExist:
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
            filter_data["bountyclaim__status__in"] = [0, 1]
            filter_data["bountyclaim__person_id__in"] = assignee

        if skills:
            filter_data["skill__parent__in"] = skills

        queryset = Challenge.objects.filter(**filter_data)
        if exclude_data:
            queryset = queryset.exclude(**exclude_data)

        return queryset.order_by(sorted_by).all()

    def get_short_description(self):
        # return a shortened version of the description text
        MAX_LEN = 90
        if len(self.description) > MAX_LEN:
            return f"{self.description[0:MAX_LEN]}..."

        return self.description


class Bounty(TimeStampMixin, common.AttachmentAbstract):
    class BountyStatus(models.TextChoices):
        AVAILABLE = "Available"
        CLAIMED = "Claimed"
        IN_REVIEW = "In Review"
        COMPLETED = "Completed"
        CANCELLED = "Cancelled"

    title = models.CharField(max_length=400)
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE)
    description = models.TextField()
    skill = models.ForeignKey(
        "talent.Skill",
        on_delete=models.CASCADE,
        related_name="bounty_skill",
        blank=True,
        null=True,
        default=None,
    )
    expertise = models.ManyToManyField("talent.Expertise", related_name="bounty_expertise")
    points = models.PositiveIntegerField()
    status = models.CharField(
        max_length=255,
        choices=BountyStatus.choices,
        default=BountyStatus.AVAILABLE,
    )
    is_active = models.BooleanField(default=True)

    claimed_by = models.ForeignKey(
        "talent.Person",
        on_delete=models.CASCADE,
        related_name="bounty_claimed_by",
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ("-created_at",)

    @property
    def has_claimed(self):
        return self.status in [
            self.BountyStatus.COMPLETED,
            self.BountyStatus.IN_REVIEW,
            self.BountyStatus.CLAIMED,
        ]

    def get_expertise_as_str(self):
        return ", ".join([exp.name.title() for exp in self.expertise.all()])

    def __str__(self):
        return self.title

    @receiver(pre_save, sender="product_management.Bounty")
    def _pre_save(sender, instance, **kwargs):
        if instance.status == Bounty.BountyStatus.AVAILABLE:
            instance.claimed_by = None


class ChallengeDependency(models.Model):
    preceding_challenge = models.ForeignKey(to=Challenge, on_delete=models.CASCADE)
    subsequent_challenge = models.ForeignKey(to=Challenge, on_delete=models.CASCADE, related_name="Challenge")

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
            Challenge.objects.filter(productchallenge__product=instance.product).order_by("-published_id").first()
        )
        challenge.published_id = last_product_challenge.published_id + 1 if last_product_challenge else 1
        challenge.save()


class ContributorGuide(models.Model):
    product = models.ForeignKey(
        to=Product,
        on_delete=models.CASCADE,
        related_name="product_contributor_guide",
    )
    title = models.CharField(max_length=60, unique=True)
    description = models.TextField(null=True, blank=True)
    skill = models.ForeignKey(
        "talent.Skill",
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
    person = models.ForeignKey("talent.Person", on_delete=models.CASCADE)

    def get_absolute_url(self):
        return reverse("add_product_idea", kwargs={"pk": self.pk})

    def __str__(self):
        return f"{self.person} - {self.title}"


class Bug(TimeStampMixin):
    title = models.CharField(max_length=256)
    description = models.TextField()
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    person = models.ForeignKey("talent.Person", on_delete=models.CASCADE)

    def get_absolute_url(self):
        return reverse("add_product_bug", kwargs={"product_slug": self.product.slug})

    def __str__(self):
        return f"{self.person} - {self.title}"


class ProductContributorAgreementTemplate(TimeStampMixin):
    product = models.ForeignKey(
        "product_management.Product",
        related_name="contributor_agreement_templates",
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=256)
    content = models.TextField()
    effective_date = models.DateField()
    created_by = models.ForeignKey("talent.Person", on_delete=models.CASCADE)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.title} ({self.product})"


class IdeaVote(TimeStampMixin):
    voter = models.ForeignKey("security.User", on_delete=models.CASCADE)
    idea = models.ForeignKey(Idea, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("voter", "idea")


class ProductContributorAgreement(TimeStampMixin):
    agreement_template = models.ForeignKey(to=ProductContributorAgreementTemplate, on_delete=models.CASCADE)
    person = models.ForeignKey(
        to="talent.Person",
        on_delete=models.CASCADE,
        related_name="contributor_agreement",
    )
    accepted_at = models.DateTimeField(auto_now_add=True, null=True)
