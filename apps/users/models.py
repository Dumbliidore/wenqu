from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

# 各类验证码的文案、长度与有效期（ttl）：链接/短码都可能被翻出来重用，超时即作废
# 新增一种 send_type 只改这里，字段选项、发码长度和校验规则会跟着走
VERIFY_CODES = {
    "register": {"label": "注册", "length": 16, "ttl": timedelta(hours=24)},
    "forget": {"label": "找回密码", "length": 16, "ttl": timedelta(hours=24)},
    "update_email": {"label": "修改邮箱", "length": 4, "ttl": timedelta(minutes=10)},
}


class UserProfile(AbstractUser):
    nick_name = models.CharField(max_length=50, verbose_name="昵称", default="")
    birday = models.DateField(verbose_name="生日", null=True, blank=True)
    gender = models.CharField(
        max_length=7,
        choices=(("male", "男"), ("female", "女")),
        default="female",
        verbose_name="性别",
    )
    address = models.CharField(max_length=100, default="", verbose_name="地址")
    mobile = models.CharField(
        max_length=11, null=True, blank=True, verbose_name="手机号码"
    )
    image = models.ImageField(
        upload_to="image/%Y/%m",
        default="image/default.png",
        max_length=100,
        verbose_name="头像",
    )

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username

    def unread_message_nums(self):
        from operation.models import UserMessage

        return UserMessage.objects.filter(user=self.id, has_read=False).count()


class EmailVerifyRecord(models.Model):
    code = models.CharField(max_length=20, verbose_name="验证码")
    email = models.EmailField(max_length=50, verbose_name="邮箱")
    send_type = models.CharField(
        verbose_name="验证码类型",
        choices=[(key, item["label"]) for key, item in VERIFY_CODES.items()],
        max_length=15,
    )
    send_time = models.DateTimeField(verbose_name="发送时间", default=timezone.now)

    class Meta:
        verbose_name = "邮箱验证码"
        verbose_name_plural = verbose_name
        ordering = ["-send_time"]

    def __str__(self):
        return f"{self.code}({self.email})"

    @classmethod
    def usable(cls, **filters):
        """按 send_type 的有效期过滤验证码，过期记录不再参与校验。"""
        records = cls.objects.filter(**filters)
        config = VERIFY_CODES.get(filters.get("send_type"))
        if config is None:
            return records
        return records.filter(send_time__gte=timezone.now() - config["ttl"])


class Banner(models.Model):
    title = models.CharField(max_length=100, verbose_name="标题")
    image = models.ImageField(
        upload_to="banner/%Y/%m", verbose_name="轮播图", max_length=100
    )
    url = models.URLField(max_length=200, verbose_name="访问地址")
    index = models.IntegerField(default=100, verbose_name="顺序")
    add_time = models.DateTimeField(default=timezone.now, verbose_name="添加时间")

    class Meta:
        verbose_name = "轮播图"
        verbose_name_plural = verbose_name
        ordering = ["index"]

    def __str__(self):
        return self.title
