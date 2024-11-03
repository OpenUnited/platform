import os
from dotenv import load_dotenv
from pathlib import Path
import sentry_sdk

DEBUG = True

# BASE_DIR points to the "apps" directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Path to the .env file, one level above the BASE_DIR in the root of the project
ENV_DIR = BASE_DIR.parent
dotenv_path = os.path.join(ENV_DIR, ".env")

# Load .env file
load_dotenv(dotenv_path)


ALLOWED_HOSTS = []
if allowed_hosts := os.environ.get("DJANGO_ALLOWED_HOSTS"):
    ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS").split(",")

ACTUAL_APPS = [
    "apps.portal",
    "apps.product_management",
    "apps.security",
    "apps.talent",
    "apps.engagement",
    "apps.commerce",
    "apps.canopy",
    "apps.common",
    "apps.flows.challenge_authoring",
]
THIRD_PARTIES = [
    "django_htmx",
    "django_extensions",
    "django_jinja",
    "formtools",
    "storages",
    "social_django",
    "django_filters",
    "corsheaders",
    "tinymce",
]
BUILTIN_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

INSTALLED_APPS = BUILTIN_APPS + ACTUAL_APPS + THIRD_PARTIES

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "corsheaders.middleware.CorsMiddleware",
]


ROOT_URLCONF = "apps.openunited.urls"


TEMPLATES = [
    {
        "BACKEND": "django_jinja.backend.Jinja2",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "environment": "apps.openunited.jinja2.environment",
            "match_extension": ".html",
            "match_regex": r"^(?!admin/|registration/|debug_toolbar/).*",
            # Can be set to "jinja2.Undefined" or any other subclass.
            "newstyle_gettext": True,
            "extensions": [
                "jinja2.ext.do",
                "jinja2.ext.loopcontrols",
                "jinja2.ext.i18n",
                "django_jinja.builtins.extensions.CsrfExtension",
                "django_jinja.builtins.extensions.CacheExtension",
                "django_jinja.builtins.extensions.DebugExtension",
                "django_jinja.builtins.extensions.TimezoneExtension",
                "django_jinja.builtins.extensions.UrlsExtension",
                "django_jinja.builtins.extensions.StaticFilesExtension",
                "django_jinja.builtins.extensions.DjangoFiltersExtension",
            ],
            "context_processors": [
                "django.contrib.messages.context_processors.messages",
                "social_django.context_processors.backends",
                "social_django.context_processors.login_redirect",
            ],
            "bytecode_cache": {
                "name": "default",
                "backend": "django_jinja.cache.BytecodeCache",
                "enabled": False,
            },
            "autoescape": True,
            "auto_reload": False,
            "translation_engine": "django.utils.translation",
        },
    },
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "social_django.context_processors.backends",
                "social_django.context_processors.login_redirect",
            ],
        },
    },
]

WSGI_APPLICATION = "apps.openunited.wsgi.application"


# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.environ.get("POSTGRES_DB", "ou_db"),
        "USER": os.environ.get("POSTGRES_USER", "postgres"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "postgres"),
        "HOST": os.environ.get("POSTGRES_HOST", "127.0.0.1"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

AUTH_USER_MODEL = "security.User"

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)


if not os.getenv("AWS_STORAGE_BUCKET_NAME"):
    STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
    STATIC_URL = "static/"
    STATICFILES_DIRS = [
        BASE_DIR / "static",
    ]
    MEDIA_URL = "/media/"
    MEDIA_ROOT = os.path.join(BASE_DIR, "media")

PERSON_PHOTO_UPLOAD_TO = "avatars/"
# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

INTERNAL_IPS = [
    "127.0.0.1",
]

SESSION_COOKIE_AGE = 30 * 24 * 60 * 60  # 30 days in seconds

# Adds prefix to the admin URL
# For instance, when ADMIN_CONTEXT="abc", the admin url will
# be accessible via http://<domain_name>/abc/admin
# Note: Don't include slash
ADMIN_CONTEXT = os.getenv("ADMIN_CONTEXT", None)

AUTHENTICATION_BACKENDS = []

AUTH_PROVIDER = os.getenv("AUTH_PROVIDER", "django")
if AUTH_PROVIDER == "django":
    AUTHENTICATION_BACKENDS += [
        "apps.security.backends.EmailOrUsernameModelBackend",
    ]

elif AUTH_PROVIDER == "AzureAD":
    AUTHENTICATION_BACKENDS += [
        "social_core.backends.azuread.AzureADOAuth2",
    ]
else:
    raise ValueError("Invalid value for AUTH_PROVIDER. Supported values are 'django' or 'AzureAD'.")

# social auth config
SOCIAL_AUTH_JSONFIELD_ENABLED = True
SOCIAL_AUTH_USER_MODEL = "security.User"
SOCIAL_AUTH_JSONFIELD_CUSTOM = "django.db.models.JSONField"

# Below two values should be retrieved from Microsoft Azure Portal

# Application (client) ID
SOCIAL_AUTH_AZUREAD_OAUTH2_KEY = os.getenv("AZURE_AD_CLIENT_ID")
# Directory (tenant) ID
SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_TENANT_ID = os.getenv("AZURE_AD_TENANT_ID")
# Certificates & secrets -> Client Secrets -> Value
SOCIAL_AUTH_AZUREAD_OAUTH2_SECRET = os.getenv("AZURE_AD_CLIENT_SECRET")
SOCIAL_AUTH_LOGIN_REDIRECT_URL = os.getenv("REDIRECT_URI", "/bounties")
AZUREAD_OAUTH2_SOCIAL_AUTH_RAISE_EXCEPTIONS = True
SOCIAL_AUTH_RAISE_EXCEPTIONS = True
RAISE_EXCEPTIONS = True
SOCIAL_AUTH_PIPELINE = (
    "social_core.pipeline.social_auth.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.auth_allowed",
    "social_core.pipeline.social_auth.social_user",
    "social_core.pipeline.user.get_username",
    "social_core.pipeline.social_auth.associate_by_email",
    "social_core.pipeline.user.create_user",
    "talent.pipelines.create_person",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "social_core.pipeline.user.user_details",
)

CORS_ALLOWED_ORIGINS = [
    "https://staging.openunited.com",
    "https://openunited.com",
    "https://demo.openunited.com",
]

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
EMAIL_HOST = "smtp.sendgrid.net"
EMAIL_HOST_USER = "apikey"  # this is exactly the value 'apikey'
EMAIL_HOST_PASSWORD = SENDGRID_API_KEY
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
DEFAULT_FROM_EMAIL = "no-reply@openunited.com"

if os.environ.get("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.environ.get("SENTRY_DSN"),
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=1.0,
    )
