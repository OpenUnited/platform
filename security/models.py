from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

from openunited.mixins import TimeStampMixin, UUIDMixin
from talent.models import Person
from commerce.models import Organisation


# This model will be used for advanced authentication methods
class User(AbstractUser, TimeStampMixin):
    full_name = models.CharField(max_length=256)
    preferred_name = models.CharField(max_length=128)

    def get_full_name(self):
        return self.full_name

    def get_short_name(self):
        return self.preferred_name


class SignUpRequest(TimeStampMixin):
    full_name = models.CharField(max_length=256)
    preferred_name = models.CharField(max_length=128)
    email = models.EmailField()
    verification_code = models.CharField(max_length=6)
    username = models.CharField(max_length=128)
    password = models.CharField()
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.full_name} - {self.username}"


class ProductPerson(TimeStampMixin, UUIDMixin):
    FOLLOWER = 0
    CONTRIBUTOR = 1
    PRODUCT_MANAGER = 2
    PRODUCT_ADMIN = 3

    ROLES = (
        (FOLLOWER, "Follower"),
        (CONTRIBUTOR, "Contributor"),
        (PRODUCT_MANAGER, "Manager"),
        (PRODUCT_ADMIN, "Admin"),
    )
    person = models.OneToOneField(Person, on_delete=models.CASCADE)
    product = models.ForeignKey("product_management.Product", on_delete=models.CASCADE)
    role = models.IntegerField(choices=ROLES, default=0)
    organisation = models.ForeignKey(
        "commerce.Organisation", on_delete=models.CASCADE, null=True, blank=True
    )

    def __str__(self):
        return f"{self.person} {self.get_role_display()} {self.product}"

    def clean(self):
        from security.services import ProductPersonService

        ProductPersonService.is_organisation_provided(self)


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
