from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.openunited.mixins import TimeStampMixin, UUIDMixin
from apps.product_management.models import Product
from apps.talent.models import Person

from .constants import DEFAULT_LOGIN_ATTEMPT_BUDGET
from .managers import UserManager


# This model will be used for advanced authentication methods
class User(AbstractUser, TimeStampMixin):
    remaining_budget_for_failed_logins = models.PositiveSmallIntegerField(default=3)
    password_reset_required = models.BooleanField(default=False)
    is_test_user = models.BooleanField(_("Test User"), default=False)

    objects = UserManager()

    def reset_remaining_budget_for_failed_logins(self):
        self.remaining_budget_for_failed_logins = DEFAULT_LOGIN_ATTEMPT_BUDGET
        self.save()

    def update_failed_login_budget_and_check_reset(self):
        self.remaining_budget_for_failed_logins -= 1

        if self.remaining_budget_for_failed_logins == 0:
            self.password_reset_required = True

        self.save()

    def __str__(self):
        return f"{self.username} - {self.remaining_budget_for_failed_logins} - {self.password_reset_required}"


class SignUpRequest(TimeStampMixin):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    device_hash = models.CharField(max_length=64, null=True, blank=True)
    country = models.CharField(max_length=64, null=True, blank=True)
    region_code = models.CharField(max_length=8, null=True, blank=True)
    city = models.CharField(max_length=128, null=True, blank=True)
    verification_code = models.CharField(max_length=6)
    successful = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user} - {self.successful}"


class SignInAttempt(TimeStampMixin):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    device_hash = models.CharField(max_length=64, null=True, blank=True)
    country = models.CharField(max_length=64, null=True, blank=True)
    region_code = models.CharField(max_length=8, null=True, blank=True)
    city = models.CharField(max_length=128, null=True, blank=True)
    successful = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.region_code} - {self.city} - {self.country}"


class ProductRoleAssignment(TimeStampMixin, UUIDMixin):
    class ProductRoles(models.TextChoices):
        CONTRIBUTOR = "Contributor"
        MANAGER = "Manager"
        ADMIN = "Admin"

    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, default="")
    role = models.CharField(
        max_length=255,
        choices=ProductRoles.choices,
        default=ProductRoles.CONTRIBUTOR,
    )

    def __str__(self):
        return f"{self.person} - {self.role}"


class BlacklistedUsernames(models.Model):
    username = models.CharField(max_length=30, unique=True, blank=False)

    def __str__(self):
        return self.username

    class Meta:
        db_table = "black_listed_usernames"
