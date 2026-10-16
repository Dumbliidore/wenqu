"""后台站点：unfold 主题的 AdminSite 与全局外观回调。"""

from django.conf import settings
from unfold.sites import UnfoldAdminSite

admin_site = UnfoldAdminSite(name="admin")


def environment_callback(request):
    """侧边栏用户名旁的环境标签，取代 xadmin 的 GlobalSettings。"""
    if settings.DEBUG:
        return "开发环境", "success"
    return "生产环境", "danger"
