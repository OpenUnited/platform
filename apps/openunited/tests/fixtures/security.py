from django.contrib.auth.hashers import make_password

import pytest
from model_bakery import baker

from apps.security.models import ProductRoleAssignment


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
def users(hashed_password):
    _users = baker.make("users.User", password=hashed_password, _quantity=10)
    for user in _users:
        baker.make("talent.Person", user=user)
    return _users


@pytest.fixture
def user(hashed_password):
    _user = baker.make("security.User", password=hashed_password)
    baker.make("talent.Person", user=_user)
    return _user


@pytest.fixture
@pytest.mark.django_db
def user1(hashed_password):
    _user = baker.make("security.User", password=hashed_password)
    baker.make("talent.Person", user=_user)
    return _user


@pytest.fixture
def super_user(hashed_password):
    _user = baker.make("security.User", is_superuser=True, password=hashed_password)
    baker.make("talent.Person", user=_user)
    return _user


@pytest.fixture
def product_role_assignments(user, product):
    return baker.make(
        "security.ProductRoleAssignment",
        person=user.person,
        product=product,
        _quantity=10,
    )


@pytest.fixture
def product_role_assignment(user, product):
    return baker.make(
        "security.ProductRoleAssignment",
        person=user.person,
        product=product,
    )


@pytest.fixture
def product_role_assignment_contributor(user, product):
    return baker.make(
        "security.User",
        person=user.person,
        product=product,
        role=ProductRoleAssignment.CONTRIBUTOR,
    )


@pytest.fixture
def product_role_assignment_admin(user, product):
    return baker.make(
        "security.ProductRoleAssignment",
        person=user.person,
        product=product,
        role=ProductRoleAssignment.ProductRoles.ADMIN,
    )


@pytest.fixture
def product_role_assignment_manager(user, product):
    return baker.make(
        "security.ProductRoleAssignment",
        person=user.person,
        product=product,
        role=ProductRoleAssignment.ProductRoles.MANAGER,
    )
