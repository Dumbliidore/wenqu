"""ASGI 入口，生产默认使用 settings.prod。"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.prod")

application = get_asgi_application()
