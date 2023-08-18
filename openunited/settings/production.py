from openunited.settings.base import *


SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")

EMAIL_PORT = os.environ.get("EMAIL_PORT", 587)
EMAIL_HOST = "smtp.gmail.com"
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
