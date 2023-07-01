import uuid

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from entitlements.exceptions import ValidationError as ValidError
from backend.mixins import TimeStampMixin, UUIDMixin

class Person(TimeStampMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    first_name = models.CharField(max_length=60)
    email_address = models.EmailField(null=True, blank=True)
    photo = models.ImageField(upload_to='avatars/', null=True, blank=True)
    github_username = models.CharField(max_length=30)
    git_access_token = models.CharField(max_length=60, null=True, blank=True)
    slug = models.SlugField(unique=True)
    headline = models.TextField()
    user = models.ForeignKey(to='users.User', on_delete=models.CASCADE, default=None)
    test_user = models.BooleanField(default=False, blank=True)

    class Meta:
        verbose_name_plural = 'People'

    def __str__(self):
        return self.first_name

    def get_username(self):
        if not self.user.username:
            raise AttributeError
        return self.user.username

class BountyClaim(TimeStampMixin, UUIDMixin):
    CLAIM_TYPE = (
        (CLAIM_TYPE_DONE, "Done"),
        (CLAIM_TYPE_ACTIVE, "Active"),
        (CLAIM_TYPE_FAILED, "Failed"),
        (CLAIM_TYPE_IN_REVIEW, "In review")
    )
    bounty = models.ForeignKey(Bounty, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE, blank=True, null=True)
    kind = models.IntegerField(choices=CLAIM_TYPE, default=0)
    tracker = FieldTracker()

    def __str__(self):
        return '{}: {} ({})'.format(self.bounty.challenge, self.person, self.kind)


@receiver(post_save, sender=BountyClaim)
def save_bounty_claim(sender, instance, created, **kwargs):
    challenge = instance.bounty.challenge
    reviewer = getattr(challenge, "reviewer", None)
    contributor = instance.person
    contributor_email = contributor.email_address
    reviewer_user = reviewer.user if reviewer else None

    if not created:
        # contributor has submitted the work for review
        if instance.kind == CLAIM_TYPE_IN_REVIEW and instance.tracker.previous("kind") is not CLAIM_TYPE_IN_REVIEW:
            challenge = instance.bounty.challenge
            subject = f"The challenge \"{challenge.title}\" is ready to review"
            message = f"You can see the challenge here: {challenge.get_challenge_link()}"
            if reviewer:
                notify.send(instance, recipient=reviewer_user, verb=subject, description=message)
                notification.tasks.send_notification.delay([Notification.Type.EMAIL],
                                                           Notification.EventType.TASK_READY_TO_REVIEW,
                                                           receivers=[reviewer.id],
                                                           task_title=challenge.title,
                                                           task_link=challenge.get_challenge_link())


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
    bounty_claim = models.ForeignKey(BountyClaim, on_delete=models.CASCADE, blank=True, null=True,
                                   related_name="delivery_attempt")
    person = models.ForeignKey(Person, on_delete=models.CASCADE, blank=True, null=True)
    is_canceled = models.BooleanField(default=False)
    delivery_message = models.CharField(max_length=2000, default=None)
    tracker = FieldTracker()


class BountyDeliveryAttachment(models.Model):
    bounty_delivery_attempt = models.ForeignKey(BountyDeliveryAttempt, on_delete=models.CASCADE, related_name='attachments')
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
        message = f"A new bounty delivery attempt has been created for the challenge: \"{bounty_claim.bounty.challenge.title}\""

        if reviewer:
            notify.send(instance, recipient=reviewer_user, verb=subject, description=message)
            notification.tasks.send_notification.delay([Notification.Type.EMAIL],
                                                       Notification.EventType.TASK_DELIVERY_ATTEMPT_CREATED,
                                                       receivers=[reviewer.id],
                                                       task_title=bounty_claim.bounty.challenge.title)
    if not created:
        # contributor quits the task
        if instance.is_canceled and not instance.tracker.previous("is_canceled"):
            subject = f"The contributor left the task"
            message = f"The contributor has left the task \"{bounty_claim.bounty.challenge.title}\""

            if reviewer:
                notify.send(instance, recipient=reviewer_user, verb=subject, description=message)
                notification.tasks.send_notification.delay([Notification.Type.EMAIL],
                                                           Notification.EventType.CONTRIBUTOR_LEFT_TASK,
                                                           receivers=[reviewer.id],
                                                           task_title=bounty_claim.bounty.challenge.title)

class Review(TimeStampMixin, UUIDMixin):
    product = models.ForeignKey('work.Product', on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    initiative = models.ForeignKey('work.Initiative', on_delete=models.CASCADE, null=True, blank=True)
    score = models.DecimalField(decimal_places=2, max_digits=3)
    text = models.TextField()
    created_by = models.ForeignKey(Person, on_delete=models.CASCADE, blank=True, null=True, related_name="given")


class PersonAvatar(models.Model):
    avatar = models.CharField(max_length=150)


class PersonProfile(TimeStampMixin, UUIDMixin):
    person = models.ForeignKey(Person, on_delete=models.CASCADE, blank=True, null=True, related_name="profile")
    overview = models.TextField()
    avatar = models.OneToOneField(PersonAvatar, blank=True, on_delete=models.CASCADE, default=None, null=True)


class PersonWebsite(models.Model):
    WebsiteType = (
        (0, "Personal"),
        (1, "Company")
    )
    website = models.CharField(max_length=200) 
    type = models.IntegerField(choices=WebsiteType)
    person = models.ForeignKey(PersonProfile, blank=True, null=True, default=None, on_delete=models.CASCADE,
                               related_name="websites")


class PersonSkill(models.Model):
    category = ArrayField(models.CharField(max_length=300, blank=True, null=True), default=list, blank=True, null=True)
    expertise = ArrayField(models.CharField(max_length=300, blank=True, null=True), default=list, blank=True, null=True)
    person_profile = models.ForeignKey(PersonProfile, on_delete=models.CASCADE, blank=True, null=True, default=None,
                                       related_name="skills")


class PersonSocial(TimeStampMixin, UUIDMixin):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    url = models.CharField(max_length=255)


class SocialAccount(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, default=None)

    provider = models.CharField(verbose_name=_('provider'), max_length=30)

    uid = models.CharField(verbose_name=_('uid'), max_length=settings.UID_MAX_LENGTH)
    last_login = models.DateTimeField(verbose_name=_('last login'),
                                      auto_now=True,
                                      blank=True)
    date_joined = models.DateTimeField(verbose_name=_('date joined'),
                                       auto_now_add=True,
                                       blank=True)
    extra_data = models.JSONField(verbose_name=_('extra data'), default=dict)

    class Meta:
        unique_together = ('provider', 'uid')


class PersonPreferences(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="preferences")
    send_me_challenges = models.BooleanField(default=True)