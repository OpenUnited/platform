import re
import uuid

from django.contrib import auth
from django.contrib.auth.models import AbstractBaseUser
from django.core.validators import RegexValidator
from django.db import models
from openunited.mixins import TimeStampMixin, UUIDMixin
from talent.models import Person
from product_management.models import ProductRole
from commerce.models import Organisation
from django.core.exceptions import ValidationError
from .managers import UserManager


class OrganisationPerson(TimeStampMixin, UUIDMixin):
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    right = models.IntegerField(choices=ProductRole.RIGHTS, default=0)

    def __str__(self):
        return "{} is {} of {}".format(self.person, self.right, self.organisation)


class ProductOwner(TimeStampMixin, UUIDMixin):
    organisation = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, blank=True, null=True, default=None
    )
    person = models.ForeignKey(Person, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return (
            f"Person: {self.person.first_name}"
            if self.person
            else f"Organization: {self.organisation.name}"
        )

    def clean(self):
        if not self.organisation and not self.person:
            raise ValidationError("Please select person or organisation")

    def get_username(self):
        try:
            if not self.person:
                return self.organisation.get_username()
            return self.person.get_username()
        except AttributeError:
            return self.organisation.get_username()
        except BaseException:
            return ""

    @classmethod
    def get_or_create(cls, person):
        try:
            return cls.objects.get(person=person)
        except cls.DoesNotExist:
            obj = cls.objects.create(person=person)
            return obj


class BlacklistedUsernames(models.Model):
    username = models.CharField(max_length=30, unique=True, blank=False)

    def __str__(self):
        return self.username

    class Meta:
        db_table = "black_listed_usernames"


# Deprecated, please use Talent.Profile
class User(AbstractBaseUser):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_logged = models.BooleanField(default=False)
    email = models.EmailField(unique=True)
    username = models.CharField(
        max_length=39,
        unique=True,
        default="",
        validators=[
            RegexValidator(
                regex="^[a-z0-9]*$",
                message="Username may only contain letters and numbers without any spaces",
                code="invalid_username",
            )
        ],
    )

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    def has_perm(self, perm, obj=None):
        # this only needed for django admin
        return self.is_active and self.is_staff and self.is_superuser

    def has_module_perms(self, app_label):
        # this only needed for django admin
        return self.is_active and self.is_staff and self.is_superuser

    def get_all_permissions(self, obj=None):
        return _user_get_permissions(self, obj, "all")

    objects = UserManager()

    def __str__(self):
        return self.username

    class Meta:
        db_table = "users_user"


# A few helper functions for common logic between User and AnonymousUser.
def _user_get_permissions(user, obj, from_name):
    permissions = set()
    name = "get_%s_permissions" % from_name
    for backend in auth.get_backends():
        if hasattr(backend, name):
            permissions.update(getattr(backend, name)(user, obj))
    return permissions
