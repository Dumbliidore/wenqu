"""项目公共配置，由 dev / prod / test 继承。"""

import os
import sys
from pathlib import Path

import dj_database_url
from django.urls import reverse_lazy
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
APPS_DIR = BASE_DIR / "apps"

# 各 app 以短名导入（users / courses / organization / operation / utils）
sys.path.insert(0, str(APPS_DIR))

load_dotenv(BASE_DIR / ".env")

# SECURITY WARNING: 生产环境必须在 .env 中提供独立的 DJANGO_SECRET_KEY
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "insecure-dev-only-key")

ALLOWED_HOSTS = [
    host for host in os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",") if host
]

INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.inlines",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "users",
    "operation",
    "courses",
    "organization",
    "utils",
    "captcha",
    "django_ckeditor_5",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.media",
            ],
        },
    },
]

WSGI_APPLICATION = "wsgi.application"
ASGI_APPLICATION = "asgi.application"

# DATABASE_URL 为空时使用本地 SQLite；生产环境由环境变量指向 PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", "")

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(BASE_DIR / "db.sqlite3"),
        }
    }

AUTH_USER_MODEL = "users.UserProfile"

AUTHENTICATION_BACKENDS = ["users.backends.CustomBackend"]

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "index"
LOGOUT_REDIRECT_URL = "index"

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

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# 邮件凭据一律来自环境变量；注册与找回密码的链接用 SITE_BASE_URL 拼接
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.qq.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() != "false"
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "False").lower() == "true"
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER or "noreply@example.com"
SITE_BASE_URL = os.getenv("SITE_BASE_URL", "http://127.0.0.1:8000")

# CKEditor 5 —— 课程详情与机构描述使用的富文本编辑器
_custom_colors = [
    {"color": "hsl(4, 90%, 58%)", "label": "红"},
    {"color": "hsl(340, 82%, 52%)", "label": "粉"},
    {"color": "hsl(291, 64%, 42%)", "label": "紫"},
    {"color": "hsl(262, 52%, 47%)", "label": "深紫"},
    {"color": "hsl(231, 48%, 48%)", "label": "靛蓝"},
    {"color": "hsl(207, 90%, 54%)", "label": "蓝"},
]

CKEDITOR_5_FILE_UPLOAD_PERMISSION = "staff"
CKEDITOR_5_CONFIGS = {
    "default": {
        "language": {"ui": "zh-cn", "content": "zh-cn"},
        "toolbar": {
            "items": [
                "heading",
                "|",
                "bold",
                "italic",
                "underline",
                "link",
                "bulletedList",
                "numberedList",
                "blockQuote",
                "imageUpload",
            ],
            "shouldNotGroupWhenFull": True,
        },
    },
    "extends": {
        "language": {"ui": "zh-cn", "content": "zh-cn"},
        "blockToolbar": [
            "paragraph",
            "heading1",
            "heading2",
            "heading3",
            "|",
            "bulletedList",
            "numberedList",
            "|",
            "blockQuote",
        ],
        "toolbar": {
            "items": [
                "heading",
                "|",
                "bold",
                "italic",
                "underline",
                "link",
                "undo",
                "redo",
                "|",
                "bulletedList",
                "numberedList",
                "todoList",
                "|",
                "blockQuote",
                "codeBlock",
                "insertImage",
                "imageUpload",
                "mediaEmbed",
                "|",
                "fontSize",
                "fontFamily",
                "fontColor",
                "fontBackgroundColor",
                "highlight",
                "|",
                "alignment",
                "indent",
                "outdent",
                "|",
                "findAndReplace",
                "insertTable",
                "specialCharacters",
                "horizontalLine",
                "pageBreak",
                "|",
                "showBlocks",
                "sourceEditing",
                "removeFormat",
            ],
            "shouldNotGroupWhenFull": True,
        },
        "image": {
            "toolbar": [
                "imageTextAlternative",
                "imageStyle:alignLeft",
                "imageStyle:alignRight",
                "imageStyle:alignCenter",
                "imageStyle:side",
            ],
            "styles": ["full", "side", "alignLeft", "alignRight", "alignCenter"],
        },
        "table": {
            "contentToolbar": [
                "tableColumn",
                "tableRow",
                "mergeTableCells",
                "tableProperties",
                "tableCellProperties",
            ],
            "tableProperties": {
                "borderColors": _custom_colors,
                "backgroundColors": _custom_colors,
            },
            "tableCellProperties": {
                "borderColors": _custom_colors,
                "backgroundColors": _custom_colors,
            },
        },
        "heading": {
            "options": [
                {
                    "model": "paragraph",
                    "title": "段落",
                    "class": "ck-heading_paragraph",
                },
                {
                    "model": "heading1",
                    "view": "h1",
                    "title": "一级标题",
                    "class": "ck-heading_heading1",
                },
                {
                    "model": "heading2",
                    "view": "h2",
                    "title": "二级标题",
                    "class": "ck-heading_heading2",
                },
                {
                    "model": "heading3",
                    "view": "h3",
                    "title": "三级标题",
                    "class": "ck-heading_heading3",
                },
            ]
        },
        "list": {
            "properties": {
                "styles": True,
                "startIndex": True,
                "reversed": True,
            }
        },
    },
}

UNFOLD = {
    "SITE_TITLE": "问渠在线管理后台",
    "SITE_HEADER": "问渠在线",
    "SITE_SUBHEADER": "Wenqu Learning",
    "SITE_URL": "/",
    "SITE_SYMBOL": "school",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "ENVIRONMENT": "admin.environment_callback",
    # 修 unfold 侧边栏定位脚本的过滚动抖动，见 static/js/admin-sidebar-settle.js
    "SCRIPTS": [STATIC_URL + "js/admin-sidebar-settle.js"],
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "用户",
                "icon": "group",
                "separator": True,
                "items": [
                    {
                        "title": "用户",
                        "icon": "manage_accounts",
                        "link": reverse_lazy("admin:users_userprofile_changelist"),
                    },
                    {
                        "title": "权限组",
                        "icon": "groups",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                    },
                    {
                        "title": "邮箱验证码",
                        "icon": "mail",
                        "link": reverse_lazy(
                            "admin:users_emailverifyrecord_changelist"
                        ),
                    },
                    {
                        "title": "轮播图",
                        "icon": "slideshow",
                        "link": reverse_lazy("admin:users_banner_changelist"),
                    },
                ],
            },
            {
                "title": "课程",
                "icon": "menu_book",
                "separator": True,
                "items": [
                    {
                        "title": "课程",
                        "icon": "book",
                        "link": reverse_lazy("admin:courses_course_changelist"),
                    },
                    {
                        "title": "轮播课程",
                        "icon": "auto_awesome",
                        "link": reverse_lazy("admin:courses_bannercourse_changelist"),
                    },
                    {
                        "title": "章节",
                        "icon": "list_alt",
                        "link": reverse_lazy("admin:courses_lesson_changelist"),
                    },
                    {
                        "title": "视频",
                        "icon": "movie",
                        "link": reverse_lazy("admin:courses_video_changelist"),
                    },
                    {
                        "title": "课程资源",
                        "icon": "download",
                        "link": reverse_lazy("admin:courses_courseresource_changelist"),
                    },
                ],
            },
            {
                "title": "机构",
                "icon": "apartment",
                "separator": True,
                "items": [
                    {
                        "title": "课程机构",
                        "icon": "business",
                        "link": reverse_lazy("admin:organization_courseorg_changelist"),
                    },
                    {
                        "title": "教师",
                        "icon": "person",
                        "link": reverse_lazy("admin:organization_teacher_changelist"),
                    },
                    {
                        "title": "城市",
                        "icon": "location_city",
                        "link": reverse_lazy("admin:organization_citydict_changelist"),
                    },
                ],
            },
            {
                "title": "用户行为",
                "icon": "monitoring",
                "separator": True,
                "items": [
                    {
                        "title": "用户咨询",
                        "icon": "support_agent",
                        "link": reverse_lazy("admin:operation_userask_changelist"),
                    },
                    {
                        "title": "课程评论",
                        "icon": "chat",
                        "link": reverse_lazy(
                            "admin:operation_coursecomments_changelist"
                        ),
                    },
                    {
                        "title": "用户收藏",
                        "icon": "favorite",
                        "link": reverse_lazy("admin:operation_userfavorite_changelist"),
                    },
                    {
                        "title": "用户消息",
                        "icon": "notifications",
                        "link": reverse_lazy("admin:operation_usermessage_changelist"),
                    },
                    {
                        "title": "用户课程",
                        "icon": "class",
                        "link": reverse_lazy("admin:operation_usercourse_changelist"),
                    },
                ],
            },
        ],
    },
}
