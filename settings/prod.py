"""生产配置：uv run manage.py runserver --settings=settings.prod

要求环境变量：DJANGO_SECRET_KEY、DJANGO_ALLOWED_HOSTS、DATABASE_URL（PostgreSQL）。
"""

import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401,F403

DEBUG = False

if not os.getenv("DJANGO_SECRET_KEY"):
    raise ImproperlyConfigured("生产环境必须在 .env 中设置 DJANGO_SECRET_KEY")

if not ALLOWED_HOSTS:  # noqa: F405
    raise ImproperlyConfigured("生产环境必须设置 DJANGO_ALLOWED_HOSTS")

_database_engine = DATABASES["default"]["ENGINE"]  # noqa: F405
if _database_engine != "django.db.backends.postgresql":
    raise ImproperlyConfigured(
        "生产环境使用 PostgreSQL，请把 DATABASE_URL 配成 postgres://用户:密码@主机:5432/库名"
    )

# 只有部署在 Nginx/负载均衡之后才需要信任转发头
USE_X_FORWARDED_HOST = os.getenv("USE_X_FORWARDED_HOST", "False").lower() == "true"
SECURE_PROXY_SSL_HEADER = (
    ("HTTP_X_FORWARDED_PROTO", "https") if USE_X_FORWARDED_HOST else None
)

SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "True").lower() != "false"
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}
STATIC_ROOT = BASE_DIR / "staticfiles"  # noqa: F405

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": os.getenv("DJANGO_LOG_LEVEL", "INFO")},
}
