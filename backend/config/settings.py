import os
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    return [value.strip() for value in os.getenv(name, default).split(",") if value.strip()]


def env_secret(name, default=""):
    file_path = os.getenv(f"{name}_FILE", "")
    if file_path:
        return Path(file_path).read_text(encoding="utf-8").strip()
    return os.getenv(name, default)


SECRET_KEY = env_secret("DJANGO_SECRET_KEY", "unsafe-local-development-key-change-me")
ENVIRONMENT = os.getenv("DJANGO_ENV", "development")
DEBUG = env_bool("DJANGO_DEBUG", ENVIRONMENT not in {"staging", "production"})
if ENVIRONMENT == "production" and SECRET_KEY.startswith("unsafe-"):
    raise RuntimeError("DJANGO_SECRET_KEY must be configured in production")

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_filters",
    "drf_spectacular",
    "apps.common",
    "apps.accounts",
    "apps.auditlog",
    "apps.registry",
    "apps.catalogue",
    "apps.billing",
    "apps.payments",
    "apps.operations",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.auditlog.middleware.AuthenticationAuditMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.common.revenue_security.RevenueRequestLoggingMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
        "apps.operations.context_processors.notification_summary",
    ]},
}]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

database_url = os.getenv("DATABASE_URL", "")
if not database_url and os.getenv("POSTGRES_HOST"):
    DATABASES = {"default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "imsuth_paypoint"),
        "USER": os.getenv("POSTGRES_USER", "imsuth_paypoint"),
        "PASSWORD": env_secret("POSTGRES_PASSWORD"),
        "HOST": os.getenv("POSTGRES_HOST", "db"),
        "PORT": int(os.getenv("POSTGRES_PORT", "5432")),
        "CONN_MAX_AGE": 60,
        "OPTIONS": {"sslmode": os.getenv("POSTGRES_SSLMODE", "prefer")},
    }}
else:
    database_url = database_url or "sqlite:///local.sqlite3"
    parsed_db = urlparse(database_url)
    if parsed_db.scheme in {"postgres", "postgresql"}:
        DATABASES = {"default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": parsed_db.path.lstrip("/"),
            "USER": parsed_db.username,
            "PASSWORD": parsed_db.password,
            "HOST": parsed_db.hostname,
            "PORT": parsed_db.port or 5432,
            "CONN_MAX_AGE": 60,
            "OPTIONS": {"sslmode": os.getenv("POSTGRES_SSLMODE", "prefer")},
        }}
    else:
        DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "local.sqlite3"}}

AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 12}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Africa/Lagos"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/paypoint/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# The API can be checked out independently of the separately maintained frontend.
_frontend_static = Path(os.getenv("PAYPOINT_FRONTEND_STATIC_DIR") or BASE_DIR.parent / "website" / "paypoint" / "static")
STATICFILES_DIRS = [_frontend_static] if _frontend_static.is_dir() else []
STORAGES = {"staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"}}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "login"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", not DEBUG)
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = 1800
SESSION_SAVE_EVERY_REQUEST = True
CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", not DEBUG)
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", not DEBUG)
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000" if not DEBUG else "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", False)
SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", False)
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
PAYPOINT_URL_PREFIX = os.getenv("PAYPOINT_URL_PREFIX", "").rstrip("/")
FORCE_SCRIPT_NAME = PAYPOINT_URL_PREFIX or None
if PAYPOINT_URL_PREFIX:
    SESSION_COOKIE_PATH = f"{PAYPOINT_URL_PREFIX}/"
    CSRF_COOKIE_PATH = f"{PAYPOINT_URL_PREFIX}/"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend", "rest_framework.filters.SearchFilter", "rest_framework.filters.OrderingFilter"],
    "DEFAULT_PAGINATION_CLASS": "apps.common.pagination.RevenuePagination",
    "PAGE_SIZE": 25,
    "EXCEPTION_HANDLER": "apps.common.revenue_security.api_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}
SPECTACULAR_SETTINGS = {"TITLE": "IMSUTH PayPoint API", "VERSION": "1.0.0", "SERVE_INCLUDE_SCHEMA": False,
    "PREPROCESSING_HOOKS": ["apps.common.schema.canonical_api"],
    "ENUM_NAME_OVERRIDES": {
        "ApprovalStatusEnum": [("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")],
        "ReconciliationStatusEnum": [("matched", "Matched"), ("unmatched", "Unmatched"), ("amount_mismatch", "Amount mismatch"), ("manual_review", "Manual review"), ("resolved", "Resolved")],
    },
}

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TASK_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULE = {
    'aged-reconciliation-alerts': {
        'task': 'apps.common.tasks.detect_reconciliation_alerts',
        'schedule': 900.0,
        'kwargs': {'min_age_hours': 24},
    },
}
CELERY_TASK_ALWAYS_EAGER = env_bool("CELERY_TASK_ALWAYS_EAGER", DEBUG)
PAYMENT_TEST_MODE = env_bool("PAYMENT_TEST_MODE", False)
TEST_WEBHOOK_SECRET = env_secret("TEST_WEBHOOK_SECRET")
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "no-reply@localhost.invalid")
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = env_secret("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"structured": {"format": "time=%(asctime)s level=%(levelname)s logger=%(name)s message=%(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "structured"}},
    "root": {"handlers": ["console"], "level": os.getenv("LOG_LEVEL", "INFO")},
}

# Trusted public frontend location; recovery links keep secrets in the URL fragment.
PASSWORD_RECOVERY_URL = os.getenv("PASSWORD_RECOVERY_URL", "")
