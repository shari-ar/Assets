"""Django settings for the Assets backend shell."""

from pathlib import Path
import os

from dj_database_url import parse as dj_database_url_parse

BASE_DIR = Path(__file__).resolve().parent.parent

DJANGO_DEBUG = os.getenv("DJANGO_DEBUG", "1")
DEBUG = DJANGO_DEBUG == "1"

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-placeholder")

ALLOWED_HOSTS: list[str] = ["*"]


def _csv_env(name: str, default: list[str]) -> list[str]:
    value = os.getenv(name, "")
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


CORS_ALLOWED_ORIGINS = _csv_env(
    "CORS_ALLOWED_ORIGINS",
    [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost",
        "http://127.0.0.1",
    ],
)
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = _csv_env(
    "CSRF_TRUSTED_ORIGINS",
    [origin for origin in CORS_ALLOWED_ORIGINS if origin.startswith("http")],
)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "apps.auth.apps.AuthConfig",
    "apps.wallet.apps.WalletConfig",
    "apps.tickets.apps.TicketsConfig",
    "apps.payments.apps.PaymentsConfig",
    "apps.reports.apps.ReportsConfig",
    "apps.notifications.apps.NotificationsConfig",
]

AUTH_USER_MODEL = "assets_auth.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "assets_backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "assets_backend.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

if database_url := os.getenv("DATABASE_URL"):
    DATABASES["default"] = dj_database_url_parse(database_url, conn_max_age=600, ssl_require=False)

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

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"

STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


ACCESS_TOKEN_LIFETIME_MINUTES = _env_int("ACCESS_TOKEN_LIFETIME_MINUTES", 15)
REFRESH_TOKEN_LIFETIME_DAYS = _env_int("REFRESH_TOKEN_LIFETIME_DAYS", 14)

AUTH_COOKIE_SECURE = os.getenv("AUTH_COOKIE_SECURE", "1" if not DEBUG else "0") == "1"
AUTH_COOKIE_SAMESITE = os.getenv("AUTH_COOKIE_SAMESITE", "Lax")
