from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models, transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from model_utils import FieldTracker
from treebeard.mp_tree import MP_Node

import engagement.tasks
from openunited.mixins import TimeStampMixin, UUIDMixin, ProductMixin
from engagement.models import Notification
from talent.models import Person, Skill, Expertise
from product_management.utils import get_person_data, to_dict


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
        # update challengelisting when capability info is updated
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


class Product(ProductMixin):
    attachment = models.ManyToManyField(Attachment, related_name="product_attachments", blank=True)
    capability_start = models.ForeignKey(Capability, on_delete=models.CASCADE, null=True, editable=False)
    owner = models.ForeignKey('commercial.ProductOwner', on_delete=models.CASCADE, null=True)

    def get_members_emails(self):
        return self.productrole_set.all().values_list("person__email_address", flat=True)

    def get_members_ids(self):
        return self.productrole_set.all().values_list("person__id", flat=True)

    def is_product_member(self, person):
        return self.productrole_set.filter(person=person).exists()

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

    def get_available_challenges_count(self):
        return self.challenge_set.filter(status=Challenge.CHALLENGE_STATUS_AVAILABLE).count()

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


@receiver(post_save, sender=Initiative)
def save_initiative(sender, instance, created, **kwargs):
    if not created:
        # update challengelisting when initiative info is updated
        ChallengeListing.objects.filter(initiative=instance).update(initiative_data=to_dict(instance))


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
        (CHALLENGE_STATUS_IN_REVIEW, "In review")
    )
    CHALLENGE_PRIORITY = (
        (0, 'High'),
        (1, 'Medium'),
        (2, 'Low')
    )

    SKILL_MODE = (
        (0, 'Single Skill'),
        (1, 'Multiple Skills')
    )

    REWARD_TYPE = (
        (0, 'Liquid Points'),
        (1, 'Non-liquid Points'),
    )

    initiative = models.ForeignKey(Initiative, on_delete=models.SET_NULL, blank=True, null=True)
    capability = models.ForeignKey(Capability, on_delete=models.SET_NULL, blank=True, null=True)
    title = models.TextField()
    description = models.TextField()
    short_description = models.TextField(max_length=256)
    status = models.IntegerField(choices=CHALLENGE_STATUS, default=0)
    attachment = models.ManyToManyField(Attachment, related_name="challenge_attachements", blank=True)
    tag = models.ManyToManyField(Tag, related_name="challenge_tags", blank=True)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name="challenge",
                                 blank=True, null=True, default=None)
    expertise = models.ManyToManyField(Expertise, related_name="challenge_expertise")
    blocked = models.BooleanField(default=False)
    featured = models.BooleanField(default=False)
    priority = models.IntegerField(choices=CHALLENGE_PRIORITY, default=1)
    published_id = models.IntegerField(default=0, blank=True, editable=False)
    auto_approve_task_claims = models.BooleanField(default=True)
    created_by = models.ForeignKey("talent.Person", on_delete=models.CASCADE, blank=True, null=True,
                                   related_name="created_by")
    updated_by = models.ForeignKey("talent.Person", on_delete=models.CASCADE, blank=True, null=True,
                                   related_name="updated_by")
    tracker = FieldTracker()
    comments_start = models.ForeignKey(to="comments.challengecomment", on_delete=models.SET_NULL, null=True, editable=False)
    reviewer = models.ForeignKey("talent.Person", on_delete=models.SET_NULL, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    video_url = models.URLField(blank=True, null=True)
    contribution_guide = models.ForeignKey("contribution_management.ContributorGuide",
                                           null=True,
                                           default=None,
                                           blank=True,
                                           on_delete=models.SET_NULL)
    skill_mode = models.IntegerField(choices=SKILL_MODE, default=0)
    reward_type = models.IntegerField(choices=REWARD_TYPE, default=1)

    class Meta:
        verbose_name_plural = "Challenges"

    def __str__(self):
        return self.title

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


@receiver(post_save, sender=Challenge)
def save_challenge(sender, instance, created, **kwargs):
    # If challenge changed status to available/claimed/done
    try:
        reviewer = instance.reviewer

        # set contributor role for user if task is done
        if instance.status == Challenge.CHALLENGE_STATUS_DONE and \
            instance.tracker.previous('status') != Challenge.CHALLENGE_STATUS_DONE:
            try:
                bounty_claim = instance.taskclaim_set.filter(kind=0).first()
                if bounty_claim:
                    product_person_data = dict(
                        product_id=instance.product.id,
                        person_id=bounty_claim.person.id
                    )
                    if not ProductRole.objects.filter(**product_person_data,
                                                        right__in=[ProductRole.PERSON_TYPE_CONTRIBUTOR,
                                                                   ProductRole.PERSON_TYPE_PRODUCT_ADMIN,
                                                                   ProductRole.PERSON_TYPE_PRODUCT_MANAGER]).exists():
                        with transaction.atomic():
                            ProductRole.objects.create(**product_person_data,
                                                         right=ProductRole.PERSON_TYPE_CONTRIBUTOR)
            except Exception as e:
                print("Failed to change a user role", e, flush=True)

        if instance.tracker.previous('status') != instance.status \
                and instance.status == Challenge.CHALLENGE_STATUS_CLAIMED \
                and reviewer:
            notification.tasks.send_notification.delay([Notification.Type.EMAIL],
                                                       Notification.EventType.TASK_STATUS_CHANGED,
                                                       receivers=[reviewer.id],
                                                       title=instance.title,
                                                       link=instance.get_challenge_link())
    except Person.DoesNotExist:
        pass
    
    
    has_bountyclaim_in_review = False
    for bounty in instance.bounty_set.all():
        if bounty.bountyclaim_set.filter(kind=0).count() > 0:
            has_bountyclaim_in_review = True

    challenge_listing_data = dict(
        title=instance.title,
        description=instance.description,
        short_description=instance.short_description,
        status=instance.status,
        tags=list(instance.tag.all().values_list('name', flat=True)),
        blocked=instance.blocked,
        featured=instance.featured,
        priority=instance.priority,
        published_id=instance.published_id,
        auto_approve_task_claims=instance.auto_approve_task_claims,
        task_creator_id=str(instance.created_by.id) if instance.created_by.id else None,
        created_by=get_person_data(instance.created_by),
        updated_by=get_person_data(instance.updated_by),
        reviewer=get_person_data(instance.reviewer) if instance.reviewer else None,
        product_data={
            "name": instance.product.name,
            "slug": instance.product.slug,
            "owner": instance.product.get_product_owner().username,
            "website": instance.product.website,
            "detail_url": instance.product.detail_url,
            "video_url": instance.product.video_url
        } if instance.product else None,
        product=instance.product,
        has_active_depends=Challenge.objects.filter(challengedepend__challenge=instance.id).exclude(
            status=Challenge.CHALLENGE_STATUS_DONE).exists(),
        initiative_id=instance.initiative.id if instance.initiative else None,
        initiative_data=to_dict(instance.initiative) if instance.initiative else None,
        capability_id=instance.capability.id if instance.capability is not None else None,
        capability_data=to_dict(instance.capability) if instance.capability else None,
        in_review=has_bountyclaim_in_review,
        video_url=instance.video_url,
    )

    # task_claim = instance.taskclaim_set.filter(kind__in=[0, 1]).first()
    all_bounty_claim = []
    for bounty in instance.bounty_set.all():
        bounty_claim = bounty.bountyclaim_set.filter(kind__in=[0, 1]).first()
        if bounty_claim:
            all_bounty_claim.append({
                'bounty_claim': bounty_claim.id, 
                'person': get_person_data(bounty_claim.person),
                'person_id': '%s'%bounty_claim.person.id})

    if len(all_bounty_claim) > 0:
        challenge_listing_data["task_claim"] = all_bounty_claim
        # challenge_listing_data["assigned_to_data"] = get_person_data(task_claim.person)
        # challenge_listing_data["assigned_to_person_id"] = task_claim.person.id if task_claim.person else None
        challenge_listing_data["assigned_to_data"] = None
        challenge_listing_data["assigned_to_person_id"] = None
    else:
        challenge_listing_data["task_claim"] = None
        challenge_listing_data["assigned_to_data"] = None
        challenge_listing_data["assigned_to_person_id"] = None

    if created:
        product = instance.product
        last_product_challenge = None
        if product:
            last_product_challenge = Challenge.objects \
                .filter(productchallenge__product=product) \
                .order_by('-published_id').last()
        published_id = last_product_challenge.published_id + 1 if last_product_challenge else 1
        instance.published_id = published_id
        instance.save()

        challenge_listing_data["published_id"] = published_id

    # create TaskListing object
    challengelisting_exist = ChallengeListing.objects.filter(challenge=instance).exists()

    if challengelisting_exist:
        ChallengeListing.objects.filter(challenge=instance).update(**challenge_listing_data)
    else:
        ChallengeListing.objects.create(
            challenge=instance,
            **challenge_listing_data
        )

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
        (BOUNTY_STATUS_IN_REVIEW, "In review")
    )

    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name="bounty_skill",
                                 blank=True, null=True, default=None)
    expertise = models.ManyToManyField(Expertise, related_name="bounty_expertise")
    points = models.IntegerField()
    status = models.IntegerField(choices=BOUNTY_STATUS, default=BOUNTY_STATUS_AVAILABLE)
    is_active = models.BooleanField(default=True)


class ChallengeListing(models.Model):
    challenge = models.OneToOneField(Challenge, on_delete=models.CASCADE, unique=True)
    title = models.TextField()
    description = models.TextField()
    short_description = models.TextField(max_length=256)
    status = models.IntegerField(choices=Challenge.CHALLENGE_STATUS, default=0)
    tags = ArrayField(ArrayField(models.CharField(max_length=254)))
    blocked = models.BooleanField(default=False)
    featured = models.BooleanField(default=False)
    priority = models.IntegerField(choices=Challenge.CHALLENGE_PRIORITY, default=1)
    published_id = models.IntegerField(default=0, blank=True, editable=False)
    auto_approve_task_claims = models.BooleanField(default=True)
    task_creator = models.ForeignKey(Person, on_delete=models.SET_NULL, related_name="creator", null=True)
    created_by = models.JSONField()
    updated_by = models.JSONField()
    reviewer = models.JSONField(null=True)
    product_data = models.JSONField(null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    video_url = models.URLField(blank=True, null=True)

    task_claim = models.JSONField(null=True)
    assigned_to_data = models.JSONField(null=True)
    assigned_to_person = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, related_name="challenge_listing")
    has_active_depends = models.BooleanField(default=False)
    initiative = models.ForeignKey(Initiative, on_delete=models.SET_NULL, null=True)
    initiative_data = models.JSONField(null=True)
    capability = models.ForeignKey(Capability, on_delete=models.SET_NULL, null=True)
    capability_data = models.JSONField(null=True)

    in_review = models.BooleanField(default=False)

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
        skills = input_data.get("skills", [])
        task_creator = input_data.get("task_creator", [])

        if statuses:
            filter_data["status__in"] = statuses

        if Challenge.CHALLENGE_STATUS_AVAILABLE in statuses:
            filter_data["has_active_depends"] = False

        if tags:
            filter_data["tags__contains"] = tags

        if skills:
            filter_data["challenge__skill__parent__in"] = skills

        if priority:
            filter_data["priority__in"] = priority

        if task_creator:
            filter_data["challenge_creator_id__in"] = task_creator

        if assignee:
            filter_data["assigned_to_person_id__in"] = assignee

        filter_data["product__is_private"] = False

        queryset = ChallengeListing.objects.filter(**filter_data)
        if exclude_data:
            queryset = queryset.exclude(**exclude_data)

        return queryset.distinct().order_by(sorted_by).all()


class ChallengeDepend(models.Model):
    challenge = models.ForeignKey(to=Challenge, on_delete=models.CASCADE, related_name='Challenge')
    depends_by = models.ForeignKey(to=Challenge, on_delete=models.CASCADE)

    class Meta:
        db_table = 'work_challenge_depend'


class ProductChallenge(TimeStampMixin, UUIDMixin):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE)


@receiver(post_save, sender=ProductChallenge)
def save_product_task(sender, instance, created, **kwargs):
    if created:
        challenge = instance.challenge
        last_product_challenge = Challenge.objects \
            .filter(productchallenge__product=instance.product) \
            .order_by('-published_id').first()
        challenge.published_id = last_product_challenge.published_id + 1 if last_product_challenge else 1
        challenge.save()
