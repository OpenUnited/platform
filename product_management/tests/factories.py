from datetime import date
from random import randint
from django.contrib.contenttypes.models import ContentType
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice, FuzzyInteger, FuzzyDate
from factory import (
    Faker,
    SubFactory,
    SelfAttribute,
    LazyAttribute,
    Sequence,
    post_generation,
)

from product_management.models import Challenge, Product, Bounty, Idea, Bug
from talent.models import BountyClaim
from talent.tests.factories import (
    PersonFactory,
    SkillFactory,
    ExpertiseFactory,
)


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
    created_by = SubFactory(PersonFactory)
    # Looping is required because we cannot pass a list of sets.
    # Integer list is required.
    status = FuzzyChoice([status[0] for status in Challenge.CHALLENGE_STATUS])
    priority = FuzzyChoice(
        [priority[0] for priority in Challenge.CHALLENGE_PRIORITY]
    )
    reward_type = FuzzyChoice([reward[0] for reward in Challenge.REWARD_TYPE])

    class Meta:
        model = Challenge


class BountyFactory(DjangoModelFactory):
    challenge = SubFactory(ChallengeFactory)
    skill = SubFactory(SkillFactory)
    points = FuzzyInteger(1, 100)
    status = FuzzyChoice([status[0] for status in Bounty.BOUNTY_STATUS])

    class Meta:
        model = Bounty

    @post_generation
    def expertise(self, create, extracted, **kwargs):
        if not create or not extracted:
            exp_list = [ExpertiseFactory() for _ in range(0, randint(1, 4))]
            self.expertise.add(*exp_list)
            return

        self.expertise.add(*extracted)


# BountyClaim model is in talent app. However, to avoid circular import error, its
# factory method is written in product_management app.
class BountyClaimFactory(DjangoModelFactory):
    bounty = SubFactory(BountyFactory)
    person = SubFactory(PersonFactory)
    expected_finish_date = FuzzyDate(
        date.today(), date.today().replace(year=date.today().year + 1)
    )
    kind = FuzzyChoice([kind[0] for kind in BountyClaim.CLAIM_TYPE])

    class Meta:
        model = BountyClaim


class ProductIdeaFactory(DjangoModelFactory):
    title = Sequence(lambda n: f"title-{n}")
    description = Faker("paragraph")
    person = SubFactory(PersonFactory)
    product = SubFactory(OwnedProductFactory)

    class Meta:
        model = Idea


class ProductBugFactory(DjangoModelFactory):
    title = Sequence(lambda n: f"title-{n}")
    description = Faker("paragraph")
    person = SubFactory(PersonFactory)
    product = SubFactory(OwnedProductFactory)

    class Meta:
        model = Bug
