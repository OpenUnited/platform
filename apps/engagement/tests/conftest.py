import pytest
from django.core.cache import cache
from django.core.management import call_command
from django.test.utils import override_settings

@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """
    Set up the test database, ensuring all required tables exist
    """
    with django_db_blocker.unblock():
        # Ensure all migrations are run, not just django_q
        call_command('migrate')

@pytest.fixture(scope='session', autouse=True)
def setup_test_environment():
    """Setup synchronous test environment"""
    # Override Django Q settings for synchronous operation
    test_settings = {
        'Q_CLUSTER': {
            'name': 'test_cluster',
            'workers': 1,
            'timeout': 30,
            'sync': True,     # Run synchronously
            'orm': 'default',
            'bulk': 1,
            'catch_up': False,
            'log_level': 'DEBUG'
        }
    }
    
    with override_settings(**test_settings):
        yield

@pytest.fixture(autouse=True)
def clean_database():
    """Clean up notifications after each test"""
    yield
    from apps.engagement.models import AppNotification, EmailNotification
    AppNotification.objects.all().delete()
    EmailNotification.objects.all().delete()

@pytest.fixture(autouse=True)
def db_access(db):
    """
    Global fixture to enable database access for all tests
    """
    pass

@pytest.fixture(autouse=True)
def clear_cache():
    """
    Clear the cache before each test
    """
    cache.clear()
    yield
    cache.clear()