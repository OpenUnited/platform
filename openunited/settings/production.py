from openunited.settings.base import *


SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")

DEBUG = False

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")

TEMPLATES[0]["OPTIONS"]["auto_reload"] = DEBUG

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = os.environ.get("EMAIL_PORT", 587)
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
