"""问渠在线 URL 配置"""

from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from users.views import (
    ActiveUserView,
    ForgetPwdView,
    IndexView,
    LoginView,
    LogOutView,
    ModifyPwdView,
    RegisterView,
    ResetView,
)

from admin import admin_site

urlpatterns = [
    path("admin/", admin_site.urls),
    path("", IndexView.as_view(), name="index"),
    path("login/", LoginView.as_view(), name="login"),
    path("register/", RegisterView.as_view(), name="register"),
    path("active/<str:active_code>/", ActiveUserView.as_view(), name="user_active"),
    path("captcha/", include("captcha.urls")),
    path("forget/", ForgetPwdView.as_view(), name="forget_pwd"),
    path("reset/<str:active_code>/", ResetView.as_view(), name="reset_pwd"),
    path("modify/", ModifyPwdView.as_view(), name="modify_pwd"),
    path("logout/", LogOutView.as_view(), name="logout"),
    path("org/", include("organization.urls", namespace="org")),
    path("course/", include("courses.urls", namespace="course")),
    path("users/", include("users.urls", namespace="users")),
    path("ckeditor5/", include("django_ckeditor_5.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = "users.views.page_not_found"
handler403 = "users.views.permission_denied"
handler500 = "users.views.page_error"
