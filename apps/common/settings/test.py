from .base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'test_db',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432',
        'ATOMIC_REQUESTS': False,
        'TEST': {
            'NAME': 'test_db',
        },
    }
}

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable migrations except for django_q
class DisableMigrations:
    def __contains__(self, item):
        return item != 'django_q'  # Allow django_q migrations

    def __getitem__(self, item):
        if item == 'django_q':
            return None  # Use normal migrations for django_q
        return 'notmigrations'  # Disable migrations for other apps

MIGRATION_MODULES = DisableMigrations()

SECRET_KEY = 'django-insecure-test-key-123'  # Only for testing

# Configure Django-Q for testing async behavior
Q_CLUSTER = {
    'name': 'TestCluster',
    'workers': 1,
    'timeout': 30,
    'queue_limit': 50,
    'bulk': 1,
    'orm': 'default',
    'sync': True,
    'catch_up': False,
    'log_level': 'DEBUG',
}

# Use synchronous event bus in tests
EVENT_BUS = {
    'BACKEND': 'apps.event_hub.services.backends.django_q.DjangoQBackend',
    'LOGGING_ENABLED': True,
    'TASK_TIMEOUT': 30,
    'SYNC_IN_TEST': False,
}

# Add detailed logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
    },
    'loggers': {
        'django_q': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
