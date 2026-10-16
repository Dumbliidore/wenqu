"""本地开发配置，manage.py 默认使用（settings.dev）。"""

from .base import *  # noqa: F401,F403

DEBUG = True

ALLOWED_HOSTS = ["*"]

# 未配置真实 SMTP 凭据时把邮件打印到控制台，注册/找回密码流程不会被卡住
if not EMAIL_HOST_USER:  # noqa: F405
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
]
