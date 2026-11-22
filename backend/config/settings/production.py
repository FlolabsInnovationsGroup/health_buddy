"""Production. Every value that matters for security is explicit here."""

from .base import *  # noqa: F403
from .base import DATABASES, env

DEBUG = False
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")  # required, no default

# TLS is terminated at the load balancer, which tells us the original scheme.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
# The load balancer's health probe speaks plain HTTP, so it must not be redirected.
SECURE_REDIRECT_EXEMPT = [r"^health/"]

SECURE_HSTS_SECONDS = env.int("DJANGO_SECURE_HSTS_SECONDS", default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
# HSTS preload is a one-way commitment for the domain; opt in deliberately later.
SILENCED_SYSTEM_CHECKS = ["security.W021"]

# Database connections: reuse them, and require TLS to PostgreSQL.
DATABASES["default"]["CONN_MAX_AGE"] = env.int("DB_CONN_MAX_AGE", default=60)
DATABASES["default"].setdefault("OPTIONS", {})["sslmode"] = env("DB_SSLMODE", default="require")
