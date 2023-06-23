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