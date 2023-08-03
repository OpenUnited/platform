from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from openunited.mixins import TimeStampMixin, UUIDMixin, AncestryMixin
from engagement.models import Notification
import engagement
from treebeard.mp_tree import MP_Node


class Person(AbstractUser, TimeStampMixin):
    photo = models.ImageField(upload_to="avatars/", null=True, blank=True)
    headline = models.TextField()
    overview = models.TextField(blank=True)
    send_me_bounties = models.BooleanField(default=True)
    current_position = models.CharField(max_length=256, null=True, blank=True)
    twitter_link = models.URLField(null=True, blank=True)
    linkedin_link = models.URLField(null=True, blank=True)
    is_test_user = models.BooleanField(_("Test User"), default=False)

    class Meta:
        db_table = "talent_person"
        verbose_name_plural = "People"

    def __str__(self):
        return self.get_full_name()


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
    skill = models.JSONField(blank=True, null=True)
    expertise = models.JSONField(blank=True, null=True)


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
    kind = models.IntegerField(choices=CLAIM_TYPE, default=0)

    def __str__(self):
        return "{}: {} ({})".format(self.bounty.challenge, self.person, self.kind)


@receiver(post_save, sender=BountyClaim)
def save_bounty_claim(sender, instance, created, **kwargs):
    challenge = instance.bounty.challenge
    reviewer = getattr(challenge, "reviewer", None)
    contributor = instance.person
    contributor_email = contributor.email_address
    reviewer_user = reviewer.user if reviewer else None

    if not created:
        # contributor has submitted the work for review
        if (
            instance.kind == BountyClaim.CLAIM_TYPE_IN_REVIEW
            and instance.tracker.previous("kind")
            is not BountyClaim.CLAIM_TYPE_IN_REVIEW
        ):
            challenge = instance.bounty.challenge
            subject = f'The challenge "{challenge.title}" is ready to review'
            message = (
                f"You can see the challenge here: {challenge.get_challenge_link()}"
            )
            if reviewer:
                engagement.tasks.send_notification.delay(
                    [Notification.Type.EMAIL],
                    Notification.EventType.BOUNTY_SUBMISSION_READY_TO_REVIEW,
                    receivers=[reviewer.id],
                    task_title=challenge.title,
                    task_link=challenge.get_challenge_link(),
                )


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


# class Review(TimeStampMixin, UUIDMixin):
#     product = models.ForeignKey('product_management.Product', on_delete=models.CASCADE)
#     person = models.ForeignKey(Person, on_delete=models.CASCADE)
#     initiative = models.ForeignKey('product_management.Initiative', on_delete=models.CASCADE, null=True, blank=True)
#     score = models.DecimalField(decimal_places=2, max_digits=3)
#     text = models.TextField()
#     created_by = models.ForeignKey(Person, on_delete=models.CASCADE, blank=True, null=True, related_name="given")
