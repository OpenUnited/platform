import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice
from factory import SubFactory

from product_management.tests.factories import (
    OwnedProductFactory,
    ProductIdeaFactory,
)
from security.models import User, ProductRoleAssignment, IdeaVote
from talent.tests.factories import PersonFactory


class UserFactory(DjangoModelFactory):
    first_name = factory.Sequence(lambda n: f"first_name{n}")
    last_name = factory.Sequence(lambda n: f"last_name{n}")
    username = factory.Sequence(lambda n: f"username{n}")
    password = factory.Sequence(lambda n: f"password{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")

    class Meta:
        model = User


class ProductRoleAssignmentFactory(DjangoModelFactory):
    person = SubFactory(PersonFactory)
    product = SubFactory(OwnedProductFactory)
    role = FuzzyChoice([elem[0] for elem in ProductRoleAssignment.ROLES])

    class Meta:
        model = ProductRoleAssignment


class IdeaVoteFactory(DjangoModelFactory):
    idea = SubFactory(ProductIdeaFactory)
    voter = SubFactory(UserFactory)

    class Meta:
        model = IdeaVote
