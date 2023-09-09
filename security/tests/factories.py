import factory
from factory.django import DjangoModelFactory

from security.models import User


class UserFactory(DjangoModelFactory):
    first_name = factory.Sequence(lambda n: f"first_name{n}")
    last_name = factory.Sequence(lambda n: f"last_name{n}")
    username = factory.Sequence(lambda n: f"username{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")

    class Meta:
        model = User
