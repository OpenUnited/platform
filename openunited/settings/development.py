import socket

from openunited.settings.base import *

DEBUG = True

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
]

TEMPLATES[0]["OPTIONS"]["auto_reload"] = DEBUG

# Required for django-debug-toolbar
hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
INTERNAL_IPS = [ip[: ip.rfind(".")] + ".1" for ip in ips] + [
    "127.0.0.1",
    "10.0.2.2",
]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_HOST = "localhost"
EMAIL_PORT = os.environ.get("EMAIL_PORT", 587)
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
