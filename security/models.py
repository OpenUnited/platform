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
