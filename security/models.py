import re
import uuid

from django.contrib import auth
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser
from django.core.validators import RegexValidator
from django.db import models
from openunited.mixins import TimeStampMixin, UUIDMixin
from talent.models import Person
from product_management.models import ProductRole
from commerce.models import Organisation
from django.core.exceptions import ValidationError

class OrganisationPerson(TimeStampMixin, UUIDMixin):
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    right = models.IntegerField(choices=ProductRole.RIGHTS, default=0)

    def __str__(self):
        return '{} is {} of {}'.format(self.person, self.right, self.organisation)

class ProductOwner(TimeStampMixin, UUIDMixin):
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, blank=True, null=True, default=None)
    person = models.ForeignKey(Person, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f"Person: {self.person.first_name}" if self.person else f"Organization: {self.organisation.name}"

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


class UserManager(BaseUserManager):
    """
    Manager for a custom User model
    """

    def create_user(self, username, email, password=None):
        if not username:
            raise ValueError("Username should be provided!")
        elif BlacklistedUsernames.objects.filter(username=username).exists():
            raise ValueError("Username is not valid!")
        elif Organisation.objects.filter(username=username).exists():
            raise ValueError("You can't have the same username as organisation name!")
        elif not re.match(r'^[a-z0-9]*$', username):
            raise ValueError("Username may only contain letters and numbers")
        user = self.model(username=username, email=email)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None):
        user = self.create_user(username, email, password)
        user.is_superuser = True
        user.is_staff = True
        user.save()
        return user


class User(AbstractBaseUser):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_logged = models.BooleanField(default=False)
    email = models.EmailField()
    username = models.CharField(max_length=39,
                                unique=True,
                                default='',
                                validators=[
                                    RegexValidator(
                                        regex="^[a-z0-9]*$",
                                        message="Username may only contain letters and numbers",
                                        code="invalid_username"
                                    )
                                ])

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def has_perm(self, perm, obj=None):
        # this only needed for django admin
        return self.is_active and self.is_staff and self.is_superuser

    def has_module_perms(self, app_label):
        # this only needed for django admin
        return self.is_active and self.is_staff and self.is_superuser

    def get_all_permissions(self, obj=None):
        return _user_get_permissions(self, obj, 'all') 

    objects = UserManager()

    def __str__(self):
        return self.username

    class Meta:
        db_table = 'users_user'


# A few helper functions for common logic between User and AnonymousUser.
def _user_get_permissions(user, obj, from_name):
    permissions = set()
    name = 'get_%s_permissions' % from_name
    for backend in auth.get_backends():
        if hasattr(backend, name):
            permissions.update(getattr(backend, name)(user, obj))
    return permissions