import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyInteger, FuzzyChoice

from talent.models import Person, Feedback, Status
from security.tests.factories import UserFactory


class PersonFactory(DjangoModelFactory):
    full_name = factory.Sequence(lambda n: f"full_name{n}")
    preferred_name = factory.Sequence(lambda n: f"preferred_name{n}")
    user = factory.SubFactory(UserFactory)
    headline = factory.Faker("sentence", nb_words=6)
    overview = factory.Faker("paragraph")

    class Meta:
        model = Person


class StatusFactory(DjangoModelFactory):
    person = factory.SubFactory(PersonFactory)
    points = FuzzyInteger(0, 10_000)

    @factory.lazy_attribute
    def name(self):
        for status in reversed(Status.STATUS_POINT_MAPPING.keys()):
            current_points = Status.STATUS_POINT_MAPPING.get(status)
            if current_points < self.points:
                return status

        return Status.DRONE

    class Meta:
        model = Status


class FeedbackFactory(DjangoModelFactory):
    recipient = factory.SubFactory(PersonFactory)
    provider = factory.SubFactory(PersonFactory)
    message = factory.Faker("paragraph")
    stars = FuzzyInteger(1, 5)

    class Meta:
        model = Feedback
