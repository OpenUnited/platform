import os
from datetime import date
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.contenttypes.fields import GenericRelation
from django.utils.translation import gettext_lazy as _
from treebeard.mp_tree import MP_Node

from openunited.settings.base import MEDIA_URL, PERSON_PHOTO_UPLOAD_TO
from openunited.mixins import TimeStampMixin, UUIDMixin, AncestryMixin
from engagement.models import Notification
import engagement


class Person(TimeStampMixin):
    full_name = models.CharField(max_length=256)
    preferred_name = models.CharField(max_length=128)
    user = models.OneToOneField(
        "security.User", on_delete=models.CASCADE, related_name="person"
    )
    products = GenericRelation("product_management.Product")
    photo = models.ImageField(upload_to=PERSON_PHOTO_UPLOAD_TO, null=True, blank=True)
    headline = models.TextField()
    overview = models.TextField(blank=True)
    location = models.TextField(max_length=128, null=True, blank=True)
    send_me_bounties = models.BooleanField(default=True)
    current_position = models.CharField(max_length=256, null=True, blank=True)
    twitter_link = models.URLField(null=True, blank=True, default="")
    linkedin_link = models.URLField(null=True, blank=True)
    github_link = models.URLField(null=True, blank=True)
    website_link = models.URLField(null=True, blank=True)
    completed_profile = models.BooleanField(default=False)

    class Meta:
        db_table = "talent_person"
        verbose_name_plural = "People"

    def get_initial_data(self):
        initial = {
            "full_name": self.full_name,
            "preferred_name": self.preferred_name,
            "headline": self.headline,
            "overview": self.overview,
            "github_link": self.github_link,
            "twitter_link": self.twitter_link,
            "linkedin_link": self.linkedin_link,
            "website_link": self.website_link,
            "send_me_bounties": self.send_me_bounties,
            "current_position": self.current_position,
            "location": self.location,
        }
        return initial

    def get_username(self):
        return self.user.username if self.user else ""

    def get_photo_url(self) -> [str, bool]:
        image_url = MEDIA_URL + PERSON_PHOTO_UPLOAD_TO + "profile-empty.png"
        requires_upload = True

        if self.photo:
            image_url = self.photo.url
            requires_upload = False

        return image_url, requires_upload

    def get_products(self):
        from product_management.models import Product

        return Product.objects.none()

    def get_absolute_url(self):
        return reverse("portfolio", args=(self.user.username,))

    def delete_photo(self) -> None:
        path = self.photo.path
        if os.path.exists(path):
            os.remove(path)

        self.photo.delete(save=True)

    def toggle_bounties(self):
        self.send_me_bounties = not self.send_me_bounties
        self.save()

    def get_full_name(self):
        return self.full_name

    def get_short_name(self):
        return self.preferred_name

    def __str__(self):
        return self.full_name


class Status(models.Model):
    DRONE = "Drone"
    HONEYBEE = "Honeybee"
    TRUSTED_BEE = "Trusted Bee"
    QUEEN_BEE = "Queen Bee"
    BEEKEEPER = "Beekeeper"

    STATUS_CHOICES = [
        (DRONE, "Drone"),
        (HONEYBEE, "Honeybee"),
        (TRUSTED_BEE, "Trusted Bee"),
        (QUEEN_BEE, "Queen Bee"),
        (BEEKEEPER, "Beekeeper"),
    ]

    STATUS_POINT_MAPPING = {
        DRONE: 0,
        HONEYBEE: 50,
        TRUSTED_BEE: 500,
        QUEEN_BEE: 2000,
        BEEKEEPER: 8000,
    }

    STATUS_PRIVILEGES_MAPPING = {
        DRONE: _("Earn points by completing bounties, submitting Ideas & Bugs"),
        HONEYBEE: _("Earn payment for payment-eligible bounties on openunited.com"),
        TRUSTED_BEE: _("Early Access to claim top tasks"),
        QUEEN_BEE: _("A grant of 1000 points for your own open product on OpenUnited"),
        BEEKEEPER: _("Invite new products to openunited.com and grant points"),
    }

    person = models.OneToOneField(
        Person, on_delete=models.CASCADE, related_name="status"
    )
    name = models.CharField(max_length=20, choices=STATUS_CHOICES, default=DRONE)
    points = models.PositiveIntegerField(default=0)

    @classmethod
    def get_privileges(cls, status: str) -> str:
        return cls.STATUS_PRIVILEGES_MAPPING.get(status)

    @classmethod
    def get_statuses(cls) -> list:
        return list(cls.STATUS_POINT_MAPPING.keys())

    @classmethod
    def get_display_points(cls, status: str) -> str:
        statuses = cls.get_statuses()

        # if `status` is the last one in `statuses`
        if status == statuses[-1]:
            return f">= {cls.get_points_for_status(status)}"

        # +1 is to get the next status
        index = statuses.index(status) + 1
        return f"< {cls.get_points_for_status(statuses[index])}"

    @classmethod
    def get_points_for_status(cls, status: str) -> str:
        return cls.STATUS_POINT_MAPPING.get(status)

    def __str__(self):
        return f"{self.name} - {self.points}"


class PersonWebsite(models.Model):
    WebsiteType = ((0, "Personal"), (1, "Company"))
    website = models.CharField(max_length=200)
    type = models.IntegerField(choices=WebsiteType)
    person = models.ForeignKey(
        Person,
        blank=True,
        null=True,
        default=None,
        on_delete=models.CASCADE,
        related_name="websites",
    )


class PersonSkill(models.Model):
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        default=None,
        related_name="skills",
    )
    # The below two fields contain a list of integers
    # ie. ids of skills and expertise such as [45, 56, 87]
    skill = models.JSONField(blank=True, null=True)
    expertise = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.person} - {self.skill} - {self.expertise}"


class Skill(AncestryMixin):
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        default=None,
        related_name="children",
    )
    active = models.BooleanField(default=False, db_index=True)
    selectable = models.BooleanField(default=False)
    display_boost_factor = models.PositiveSmallIntegerField(default=1)
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    @staticmethod
    def get_active_skills(active=True, parent=None):
        return Skill.objects.filter(active=active, parent=parent).all()

    @staticmethod
    def get_active_skill_list(active=True):
        return Skill.objects.filter(active=active, parent=None).values("id", "name")


class Expertise(AncestryMixin):
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        default=None,
        related_name="expertise_children",
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default=None,
        related_name="skill_expertise",
    )
    selectable = models.BooleanField(default=False)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    @staticmethod
    def get_skill_expertise(skill):
        return Expertise.objects.filter(skill=skill).values("id", "name")

    @staticmethod
    def get_all_expertise(parent=None):
        return Expertise.objects.filter(parent=parent).all()

    @staticmethod
    def get_all_expertise_list():
        return Expertise.objects.filter(parent=None).values("id", "name")


class BountyClaim(TimeStampMixin, UUIDMixin):
    CLAIM_TYPE_DONE = 0
    CLAIM_TYPE_ACTIVE = 1
    CLAIM_TYPE_FAILED = 2
    CLAIM_TYPE_IN_REVIEW = 3

    CLAIM_TYPE = (
        (CLAIM_TYPE_DONE, "Done"),
        (CLAIM_TYPE_ACTIVE, "Active"),
        (CLAIM_TYPE_FAILED, "Failed"),
        (CLAIM_TYPE_IN_REVIEW, "In review"),
    )
    bounty = models.ForeignKey("product_management.Bounty", on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE, blank=True, null=True)
    expected_finish_date = models.DateField(default=date.today)
    kind = models.IntegerField(choices=CLAIM_TYPE, default=0)

    def __str__(self):
        return f"{self.bounty.challenge}: {self.person} ({self.get_kind_display()})"


class Comment(MP_Node):
    person = models.ForeignKey(Person, on_delete=models.CASCADE, blank=True, null=True)
    text = models.TextField(max_length=1000)

    class Meta:
        abstract = True

    def __str__(self):
        return self.text


class ChallengeComment(Comment):
    pass


class BugComment(Comment):
    pass


class IdeaComment(Comment):
    pass


class CapabilityComment(Comment):
    pass


class BountyDeliveryAttempt(TimeStampMixin):
    SUBMISSION_TYPE_NEW = 0
    SUBMISSION_TYPE_APPROVED = 1
    SUBMISSION_TYPE_REJECTED = 2

    SUBMISSION_TYPES = (
        (SUBMISSION_TYPE_NEW, "New"),
        (SUBMISSION_TYPE_APPROVED, "Approved"),
        (SUBMISSION_TYPE_REJECTED, "Rejected"),
    )

    kind = models.IntegerField(choices=SUBMISSION_TYPES, default=0)
    bounty_claim = models.ForeignKey(
        BountyClaim,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="delivery_attempt",
    )
    person = models.ForeignKey(Person, on_delete=models.CASCADE, blank=True, null=True)
    is_canceled = models.BooleanField(default=False)
    delivery_message = models.CharField(max_length=2000, default=None)


class BountyDeliveryAttachment(models.Model):
    bounty_delivery_attempt = models.ForeignKey(
        BountyDeliveryAttempt, on_delete=models.CASCADE, related_name="attachments"
    )
    file_type = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    path = models.CharField(max_length=100)


@receiver(post_save, sender=BountyDeliveryAttempt)
def save_bounty_claim_request(sender, instance, created, **kwargs):
    bounty_claim = instance.bounty_claim
    contributor = instance.person
    contributor_id = contributor.id
    reviewer = getattr(bounty_claim.bounty.challenge, "reviewer", None)
    reviewer_user = reviewer.user if reviewer else None

    # contributor request to claim it
    if created and not bounty_claim.bounty.challenge.auto_approve_task_claims:
        subject = f"A new bounty delivery attempt has been created"
        message = f'A new bounty delivery attempt has been created for the challenge: "{bounty_claim.bounty.challenge.title}"'

        if reviewer:
            engagement.tasks.send_notification.delay(
                [Notification.Type.EMAIL],
                Notification.EventType.BOUNTY_DELIVERY_ATTEMPT_CREATED,
                receivers=[reviewer.id],
                task_title=bounty_claim.bounty.challenge.title,
            )
    if not created:
        # contributor quits the task
        if instance.is_canceled and not instance.tracker.previous("is_canceled"):
            subject = f"The contributor left the task"
            message = f'The contributor has left the task "{bounty_claim.bounty.challenge.title}"'

            if reviewer:
                engagement.tasks.send_notification.delay(
                    [Notification.Type.EMAIL],
                    Notification.EventType.CONTRIBUTOR_LEFT_TASK,
                    receivers=[reviewer.id],
                    task_title=bounty_claim.bounty.challenge.title,
                )


class Feedback(models.Model):
    # Person who recevies the feedback
    recipient = models.ForeignKey(
        Person, on_delete=models.CASCADE, related_name="feedback_recipient"
    )
    # Person who sends the feedback
    provider = models.ForeignKey(
        Person, on_delete=models.CASCADE, related_name="feedback_provider"
    )
    message = models.TextField()
    stars = models.PositiveSmallIntegerField(
        default=1,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ],
    )

    def save(self, *args, **kwargs):
        if self.recipient == self.provider:
            raise ValidationError(
                _("The recipient and the provider cannot be the same.")
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.recipient} - {self.provider} - {self.stars} - {self.message[:10]}..."
