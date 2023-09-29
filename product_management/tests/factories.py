from django.contrib.contenttypes.models import ContentType
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice
from factory import Faker, SubFactory, SelfAttribute, LazyAttribute, Sequence

from product_management.models import Challenge, Product
from talent.tests.factories import PersonFactory


class ProductFactory(DjangoModelFactory):
    name = Faker("name")
    short_description = Faker("sentence")
    full_description = Faker("paragraph")
    object_id = SelfAttribute("content_object.id")
    content_type = LazyAttribute(
        lambda o: ContentType.objects.get_for_model(o.content_object)
    )

    class Meta:
        model = Product
        exclude = ["content_object"]
        abstract = True


class OwnedProductFactory(ProductFactory):
    content_object = SubFactory(PersonFactory)

    class Meta:
        model = Product


class ChallengeFactory(DjangoModelFactory):
    title = Sequence(lambda n: f"title-{n}")
    description = Faker("paragraph")
    short_description = Faker("sentence")
    product = SubFactory(OwnedProductFactory)
    # Looping is required because we cannot pass a list of sets.
    # Integer list is required.
    status = FuzzyChoice([status[0] for status in Challenge.CHALLENGE_STATUS])
    priority = FuzzyChoice([priority[0] for priority in Challenge.CHALLENGE_PRIORITY])
    reward_type = FuzzyChoice([reward[0] for reward in Challenge.REWARD_TYPE])

    class Meta:
        model = Challenge
