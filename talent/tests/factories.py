import factory
from factory.django import DjangoModelFactory
from django.core.files.base import ContentFile

from talent.models import Person


class PersonFactory(DjangoModelFactory):
    headline = factory.Faker("sentence", nb_words=6)
    overview = factory.Faker("paragraph")
    photo = factory.LazyAttribute(
        lambda _: ContentFile(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0cIDAT\x08\xd7c\xf8\xff\xff?\xc3\x00\x00\x02n\x01^\xd2\xd6\xd8\x00\x00\x00\x00IEND\xaeB`\x82",
            name="test_image.jpg",
        )
    )

    class Meta:
        model = Person
