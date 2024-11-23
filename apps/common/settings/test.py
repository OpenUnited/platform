from .base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'test_db',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable migrations
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

SECRET_KEY = 'django-insecure-test-key-123'  # Only for testing

# Configure Django-Q for testing
Q_CLUSTER = {
    'name': 'OpenUnited_Test',
    'workers': 2,
    'timeout': 30,
    'retry': 60,
    'sync': False,
    'poll': 100,
    'orm': 'default',
    'catch_up': False,
    'bulk': 1
}

# Use synchronous event bus in tests
EVENT_BUS = {
    'BACKEND': 'apps.event_hub.services.backends.django_q.DjangoQBackend',
    'LOGGING_ENABLED': True,
    'TASK_TIMEOUT': 30,
    'SYNC_IN_TEST': True,  # Add this flag
}
