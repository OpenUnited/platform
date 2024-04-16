import os
import sentry_sdk

from openunited.settings.base import *


SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")

DEBUG = False

ALLOWED_HOSTS = os.environ.get(
    "DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost"
).split(",")

TEMPLATES[0]["OPTIONS"]["auto_reload"] = DEBUG

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
EMAIL_HOST = "smtp.sendgrid.net"
EMAIL_HOST_USER = "apikey"  # this is exactly the value 'apikey'
EMAIL_HOST_PASSWORD = SENDGRID_API_KEY
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
DEFAULT_FROM_EMAIL = "no-reply@openunited.com"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
    },
}

if os.environ.get("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.environ.get("SENTRY_DSN"),
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=1.0,
    )
