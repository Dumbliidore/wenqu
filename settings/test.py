"""测试配置：数据库固定为内存 SQLite，邮件与验证码全部本地化，不依赖外部服务。

用法：uv run manage.py test --settings=settings.test
"""

from .base import *  # noqa: F401,F403

DEBUG = False

ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# 打开后填写 "passed" 即可通过验证码校验，测试不必识别图片
CAPTCHA_TEST_MODE = True

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
