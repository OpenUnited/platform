from apps.openunited.settings.base import *

DEBUG = True
SECRET_KEY = "Test secret"
ALLOWED_HOSTS = ["*"]
TEMPLATES[0]["OPTIONS"]["auto_reload"] = DEBUG

# Required for django-debug-toolbar
INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE += [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]
