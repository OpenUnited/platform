import os

from apps.openunited.settings.base import *

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
DEBUG = False
MIDDLEWARE += [
    "whitenoise.middleware.WhiteNoiseMiddleware",
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

# When running in a DigitalOcean app, Django sits behind a proxy
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

if AWS_STORAGE_BUCKET_NAME := os.getenv("AWS_STORAGE_BUCKET_NAME"):
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL")
    AWS_S3_OBJECT_PARAMETERS = {
        "CacheControl": "max-age=86400",
    }
    AWS_STATIC_LOCATION = "openunited-static"
    AWS_MEDIA_LOCATION = "openunited-media"
    AWS_QUERYSTRING_AUTH = False
    STATICFILES_DIRS = [
        os.path.join(BASE_DIR, "static"),
    ]

    STATIC_URL = f"{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/{AWS_STATIC_LOCATION}/"
    STATICFILES_STORAGE = "apps.openunited.storage_backends.StaticStorage"
    MEDIA_URL = f"{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/{AWS_MEDIA_LOCATION}/"
    DEFAULT_FILE_STORAGE = "apps.openunited.storage_backends.PublicMediaStorage"
