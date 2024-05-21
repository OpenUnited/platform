import pytest
from django.contrib.auth.hashers import make_password
from model_bakery import baker
from django.contrib.contenttypes.models import ContentType


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    print("Enable database access for all tests")


@pytest.fixture
def password():
    return "PX1235455SAA@#123"


@pytest.fixture
def hashed_password(password):
    return make_password(password)


@pytest.fixture
def super_user(hashed_password):
    _user = baker.make(
        "users.User", is_superuser=True, password=hashed_password
    )
    baker.make("talent.Person", user=_user)
    return _user


@pytest.fixture
def auth_superuser(client, super_user, password):
    client.login(username=super_user.username, password=password)
    return super_user


@pytest.fixture
def auth_user(client, user, password):
    client.login(username=user.username, password=password),
    return user
