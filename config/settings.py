"""Django settings for the Library API.

Everything that changes between a laptop, Docker Compose and CI comes from the
environment, with the defaults from the contract's implementation guide:

    PORT           8000
    DATABASE_URL   sqlite:///library.db
    TEST_MODE      unset (off). "1" turns on POST /test/reset and X-Today
    LIBRARY_TODAY  unset. YYYY-MM-DD fixes today for the whole server
"""

import os
import re
from datetime import date
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def _library_today() -> date | None:
    value = os.environ.get("LIBRARY_TODAY", "").strip()
    if not value:
        return None
    try:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise ValueError(value)
        return date.fromisoformat(value)
    except ValueError:
        raise ImproperlyConfigured(f"LIBRARY_TODAY must be a date in the form YYYY-MM-DD, got {value!r}")


PORT = int(os.environ.get("PORT", "8000"))
HOST = os.environ.get("HOST", "127.0.0.1")
TEST_MODE = os.environ.get("TEST_MODE") == "1"
LIBRARY_TODAY = _library_today()
LIBRARY_TIME_ZONE = "Europe/London"

# The API has no sessions, cookies or admin, so the key only matters to Django internals.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "library-api-local-development-only")
DEBUG = os.environ.get("DJANGO_DEBUG") == "1"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "rest_framework",
    "library",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# Routes are declared without a trailing slash, and /books/ must not redirect to /books.
APPEND_SLASH = False

DATABASES = {
    "default": dj_database_url.parse(
        os.environ.get("DATABASE_URL") or f"sqlite:///{BASE_DIR / 'library.db'}",
        conn_max_age=60,
    )
}
if DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
    # Wait for a lock instead of failing at once when two requests write together.
    DATABASES["default"].setdefault("OPTIONS", {})["timeout"] = 20

# INTEGER ids, as in the contract's schema.sql (BigAutoField would make them BIGINT).
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

LANGUAGE_CODE = "en-gb"
TIME_ZONE = LIBRARY_TIME_ZONE
USE_I18N = False
USE_TZ = True

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_CONTENT_NEGOTIATION_CLASS": "library.api.negotiation.JsonOnly",
    "EXCEPTION_HANDLER": "library.api.exceptions.handle_exception",
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
