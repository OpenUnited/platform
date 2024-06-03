import random
import string

from django.contrib.contenttypes.models import ContentType

import pytest
from model_bakery import baker


def generate_random_string(length=10):
    return "".join(random.choice(string.ascii_letters) for _ in range(length))


@pytest.fixture
def random_email_string(length=10):
    string_random = "".join(random.choice(string.ascii_letters) for _ in range(length))
    return f"{string_random}@example.com"


@pytest.fixture
def random_string(length=10):
    return generate_random_string()


@pytest.fixture
def content_type(user):
    return baker.make(ContentType)


@pytest.fixture
def client():
    from django.test import Client

    return Client()
