import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyInteger

from talent.models import Person, Feedback, Status, Skill, Expertise, PersonSkill
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


class SkillFactory(DjangoModelFactory):
    parent = None
    name = factory.Faker("word")
    active = factory.Faker("boolean")
    selectable = factory.Faker("boolean")
    display_boost_factor = factory.Faker("pyint", min_value=1, max_value=10)

    class Meta:
        model = Skill


class ExpertiseFactory(DjangoModelFactory):
    parent = None
    skill = factory.SubFactory(SkillFactory)
    name = factory.Faker("word")
    selectable = factory.Faker("boolean")

    class Meta:
        model = Expertise


class PersonSkillFactory(DjangoModelFactory):
    person = factory.SubFactory(PersonFactory)
    skill = factory.Faker("word")
    expertise = factory.Faker("word")

    class Meta:
        model = PersonSkill
