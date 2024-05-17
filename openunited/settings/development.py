from openunited.settings.base import *

DEBUG = False
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
ALLOWED_HOSTS += ["127.0.0.1", "localhost"]
TEMPLATES[0]["OPTIONS"]["auto_reload"] = DEBUG

# Required for django-debug-toolbar
INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]

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
    STATICFILES_STORAGE = "openunited.storage_backends.StaticStorage"
    MEDIA_URL = f"{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/{AWS_MEDIA_LOCATION}/"
    DEFAULT_FILE_STORAGE = "openunited.storage_backends.PublicMediaStorage"
