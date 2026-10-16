from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

from .models import UserProfile


class CustomBackend(ModelBackend):
    """支持用户名或邮箱登录；未激活用户也返回，由登录视图提示重新激活。"""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        # 用户名唯一、邮箱不唯一，某个人的邮箱完全可能是另一个人的用户名，
        # 所以要把所有候选账号都试一遍，不能取第一条就下结论
        for user in UserProfile.objects.filter(
            Q(username=username) | Q(email=username)
        ):
            if user.check_password(password):
                return user
        return None
