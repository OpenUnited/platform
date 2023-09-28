import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice
from factory import SubFactory

from product_management.tests.factories import OwnedProductFactory
from security.models import User, ProductRoleAssignment


class UserFactory(DjangoModelFactory):
    first_name = factory.Sequence(lambda n: f"first_name{n}")
    last_name = factory.Sequence(lambda n: f"last_name{n}")
    username = factory.Sequence(lambda n: f"username{n}")
    password = factory.Sequence(lambda n: f"password{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")

    class Meta:
        model = User


# Due to a circular import, we cannot declare a person field.
# Person should be passed during the initialization of the object:
# ProductRoleAssignmentFactory(person=person)
class ProductRoleAssignmentFactory(DjangoModelFactory):
    product = SubFactory(content_object=OwnedProductFactory)
    role = FuzzyChoice([elem[0] for elem in ProductRoleAssignment.ROLES])

    class Meta:
        model = ProductRoleAssignment
