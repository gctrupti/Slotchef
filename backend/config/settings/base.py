"""Base Django settings for SlotChef backend.

Django owns all business logic, authentication, scheduling orchestration,
and database schema/migrations. Supabase is used strictly as the managed
PostgreSQL provider via standard PostgreSQL connection settings, keeping
the backend portable to any PostgreSQL host.
"""

from __future__ import annotations

import os
import sys
from datetime import timedelta
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
REPO_ROOT = BASE_DIR.parent
OPTIMIZER_DIR = REPO_ROOT / "optimizer"

if str(OPTIMIZER_DIR) not in sys.path:
    sys.path.insert(0, str(OPTIMIZER_DIR))

load_dotenv(REPO_ROOT / ".env", override=False)


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return float(raw)


def _env_list(name: str, default: list[str]) -> list[str]:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return [item.strip() for item in raw.split(",") if item.strip()]


def build_postgres_config(database_url: str | None = None) -> dict:
    """Build a portable Django PostgreSQL database config from environment variables."""
    conn_max_age = _env_int("DB_CONN_MAX_AGE", 60)
    conn_health_checks = _env_bool("DB_CONN_HEALTH_CHECKS", True)
    disable_server_side_cursors = _env_bool("DB_DISABLE_SERVER_SIDE_CURSORS", False)
    sslmode = os.environ.get("DB_SSLMODE", "require").strip() or "require"
    connect_timeout = _env_int("DB_CONNECT_TIMEOUT", 10)

    url = (database_url or os.environ.get("DATABASE_URL", "")).strip()
    if url:
        config = dj_database_url.parse(
            url,
            conn_max_age=conn_max_age,
            conn_health_checks=conn_health_checks,
        )
    else:
        config = {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("POSTGRES_DB", "postgres"),
            "USER": os.environ.get("POSTGRES_USER", "postgres"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
            "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
            "PORT": os.environ.get("POSTGRES_PORT", "5432"),
            "CONN_MAX_AGE": conn_max_age,
            "CONN_HEALTH_CHECKS": conn_health_checks,
        }

    config["DISABLE_SERVER_SIDE_CURSORS"] = disable_server_side_cursors
    options = dict(config.get("OPTIONS") or {})
    if config.get("ENGINE") == "django.db.backends.postgresql":
        options.setdefault("sslmode", sslmode)
        options.setdefault("connect_timeout", connect_timeout)
        config["OPTIONS"] = options
    return config


SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "insecure-dev-only-key-change-before-deploying",
)
DEBUG = _env_bool("DJANGO_DEBUG", False)
ALLOWED_HOSTS = _env_list("DJANGO_ALLOWED_HOSTS", ["localhost", "127.0.0.1"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
    # Domain modules (modular monolith)
    "apps.identity",
    "apps.communities",
    "apps.households",
    "apps.cooks",
    "apps.bookings",
    "apps.scheduling",
    "apps.visits",
    "apps.operations",
    "apps.audit",
    "apps.finance",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": build_postgres_config(),
}

AUTH_USER_MODEL = "identity.User"

AUTHENTICATION_BACKENDS = [
    "apps.identity.backends.EmailOrPhoneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
    "EXCEPTION_HANDLER": "config.exceptions.structured_exception_handler",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=_env_int("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", 30)
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=_env_int("JWT_REFRESH_TOKEN_LIFETIME_DAYS", 7)
    ),
    "ROTATE_REFRESH_TOKENS": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "SlotChef Backend API",
    "DESCRIPTION": (
        "Authoritative Django REST API and OR-Tools CP-SAT scheduling backend "
        "for SlotChef household cooking coordination."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "ENUM_NAME_OVERRIDES": {
        "RecurringWeekdayEnum": "apps.cooks.models.CookAvailability.WEEKDAY_CHOICES",
        "VerificationStatusEnum": "apps.cooks.models.CookVerificationProfile.STATUS_CHOICES",
        "IncidentReportStatusEnum": "apps.visits.models.IncidentReport.STATUS_CHOICES",
        "IncidentAppealStatusEnum": "apps.visits.models.IncidentAppeal.STATUS_CHOICES",
        "SOSIncidentStatusEnum": "apps.visits.models.SOSIncident.STATUS_CHOICES",
        "AdminInvitationStatusEnum": "apps.identity.models.AdminInvitation.STATUS_CHOICES",
        "OTPChannelEnum": "apps.identity.models.OTPVerification.CHANNEL_CHOICES",
        "NotificationChannelEnum": "apps.visits.models.SafetyNotificationLog.CHANNEL_CHOICES",
    },
}

# Celery / Redis
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_TASK_ALWAYS_EAGER = _env_bool("CELERY_TASK_ALWAYS_EAGER", True)

# Scheduling & Reliability Policies
SOLVER_TIME_LIMIT_SECONDS = _env_float("SOLVER_TIME_LIMIT_SECONDS", 5.0)
DEFAULT_TRANSITION_MINUTES = _env_int("DEFAULT_TRANSITION_MINUTES", 5)
SCHEDULER_MAX_RETRIES = _env_int("SCHEDULER_MAX_RETRIES", 3)
IDEMPOTENCY_TTL_HOURS = _env_int("IDEMPOTENCY_TTL_HOURS", 24)

# CORS (Cross-Origin Resource Sharing)
CORS_ALLOW_ALL_ORIGINS = _env_bool("CORS_ALLOW_ALL_ORIGINS", True)
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "idempotency-key",
]


