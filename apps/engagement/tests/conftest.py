import pytest
from django.core.cache import cache

@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Global fixture to enable database access for all tests.
    This removes the need to specify @pytest.mark.django_db for each test.
    """
    pass

@pytest.fixture(autouse=True)
def use_transaction_db(transactional_db):
    """
    Global fixture to make all tests transactional.
    Similar to TransactionTestCase but pytest-style.
    """
    pass

@pytest.fixture(autouse=True)
def clear_cache():
    """
    Clear the cache before each test.
    """
    cache.clear()
    yield
    cache.clear()