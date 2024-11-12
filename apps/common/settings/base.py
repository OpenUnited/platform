import os
from dotenv import load_dotenv
from pathlib import Path
import sentry_sdk
from django.core.exceptions import ImproperlyConfigured

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

PLATFORM_APPS = [
    "apps.marketing",
    "apps.portal",
    "apps.capabilities.product_management",
    "apps.capabilities.security",
    "apps.capabilities.talent",
    "apps.engagement",
    "apps.capabilities.commerce",
    "apps.canopy",
    "apps.common",
    "apps.flows.challenge_authoring",
]
THIRD_PARTIES = [
    "django_htmx",
    "django_extensions",
    "formtools",
    "storages",
    "social_django",
    "django_filters",
    "corsheaders",
    "tinymce",
    "csp",
]
BUILTIN_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

INSTALLED_APPS = BUILTIN_APPS + PLATFORM_APPS + THIRD_PARTIES

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
    "csp.middleware.CSPMiddleware",
]


ROOT_URLCONF = "apps.common.urls"


TEMPLATES = [
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
            "debug": True,
        },
    },
]

WSGI_APPLICATION = "apps.common.wsgi.application"


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

AUTH_USER_MODEL = 'security.User'

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
        "apps.capabilities.security.backends.EmailOrUsernameModelBackend",
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
    "apps.capabilities.talent.pipelines.create_person",
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

# Authentication settings
LOGIN_URL = '/security/sign-in/'
LOGIN_REDIRECT_URL = '/'

# CSP settings
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-inline'",
    "'unsafe-eval'",
    "https://cdn.quilljs.com",
    "https://cdn.tailwindcss.com",
    "https://cdnjs.cloudflare.com",
    "https://cdn.jsdelivr.net",
    "openunited-staging.s3.amazonaws.com",
    "https://ams3.digitaloceanspaces.com",
)
CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",
    "https://cdn.quilljs.com",
    "https://cdn.tailwindcss.com",
    "https://cdnjs.cloudflare.com",
    "https://rsms.me",
    "https://cdn.jsdelivr.net",
    "openunited-staging.s3.amazonaws.com",
    "https://ams3.digitaloceanspaces.com",
)
CSP_FONT_SRC = (
    "'self'",
    "https://rsms.me",
    "https://cdn.tailwindcss.com",
)
CSP_IMG_SRC = (
    "'self'",
    "data:",
    "https:",
)
CSP_FRAME_SRC = (
    "'self'",
    "https://www.youtube.com",
)
CSP_CONNECT_SRC = (
    "'self'",
    "https://cdn.quilljs.com",
    "https://cdn.jsdelivr.net",
)

# If using AWS S3 or similar, add the domain to the CSP
if os.getenv("AWS_STORAGE_BUCKET_NAME"):
    aws_bucket_domain = f'{os.getenv("AWS_STORAGE_BUCKET_NAME")}.s3.amazonaws.com'
    CSP_DEFAULT_SRC += (aws_bucket_domain,)
    CSP_IMG_SRC += (aws_bucket_domain,)
    CSP_SCRIPT_SRC += (aws_bucket_domain,)
    CSP_STYLE_SRC += (aws_bucket_domain,)

# Add CORS settings if not already present
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_WHITELIST = CORS_ALLOWED_ORIGINS  # Use your existing CORS_ALLOWED_ORIGINS

# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Update storage section to handle both S3 and DigitalOcean Spaces
STORAGE_DOMAINS = [
    "openunited-staging.s3.amazonaws.com",
    "https://ams3.digitaloceanspaces.com",
]

if os.getenv("AWS_STORAGE_BUCKET_NAME"):
    aws_bucket_domain = f'{os.getenv("AWS_STORAGE_BUCKET_NAME")}.s3.amazonaws.com'
    STORAGE_DOMAINS.append(aws_bucket_domain)
    
    CSP_DEFAULT_SRC += tuple(STORAGE_DOMAINS)
    CSP_IMG_SRC += tuple(STORAGE_DOMAINS)
    CSP_SCRIPT_SRC += tuple(STORAGE_DOMAINS)
    CSP_STYLE_SRC += tuple(STORAGE_DOMAINS)
