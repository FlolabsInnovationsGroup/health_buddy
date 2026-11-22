"""Settings shared by every environment.

Environment-specific values come from environment variables (see .env.example).
Nothing secret lives in this file. Required values have no default on purpose,
so a missing one stops the app at start-up instead of running insecurely.
"""

from pathlib import Path

import environ

# This file is backend/config/settings/base.py: parents[2] is backend/, parents[3] is the repo root.
BASE_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BASE_DIR.parent

env = environ.Env()

# Local development: load the repo-root .env if it exists. Real environment variables
# always win, and production injects its variables directly (no file).
_env_file = REPO_ROOT / ".env"
if _env_file.is_file():
    environ.Env.read_env(_env_file)

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = False  # development.py turns it on
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])

# --- Applications ---------------------------------------------------------------
# One Django app per domain (see README section 4). Apps talk through service
# functions, never by reaching into each other's tables.
LOCAL_APPS = [
    "apps.common",
    "apps.identity",
    "apps.organizations",
    "apps.consent",
    "apps.health_records",
    "apps.data_ingestion",
    "apps.evaluations",
    "apps.conversations",
    "apps.ai_gateway",
    "apps.audit",
]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rest_framework",
    *LOCAL_APPS,
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# --- Database -------------------------------------------------------------------
# PostgreSQL via DATABASE_URL. ATOMIC_REQUESTS keeps each request all-or-nothing.
DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"]["ATOMIC_REQUESTS"] = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- API ------------------------------------------------------------------------
# Deny by default: every endpoint needs an authenticated user unless it opts out.
# No authentication class is configured yet, so until the identity app lands only
# endpoints that explicitly allow anonymous access (the health checks) respond.
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
}

# --- Passwords ------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Internationalisation -------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_TZ = True

# --- Logging --------------------------------------------------------------------
# Never log health values or personal identifiers (README section 8).
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "standard"},
    },
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", default="INFO")},
}
