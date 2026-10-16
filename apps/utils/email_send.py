import secrets

from django.conf import settings
from django.core.mail import send_mail
from users.models import VERIFY_CODES, EmailVerifyRecord

_CHARS = "AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789"


def random_str(length):
    return "".join(secrets.choice(_CHARS) for _ in range(length))


def send_register_email(email, send_type="register"):
    """生成验证码并把邮件发给收件人本身，正文链接指向当前站点。"""
    # 先校验类型再落库，否则未知类型会留下一条永远用不上的验证码
    config = VERIFY_CODES.get(send_type)
    if config is None:
        raise ValueError(f"未知的验证码类型: {send_type}")

    code = random_str(config["length"])
    EmailVerifyRecord.objects.create(code=code, email=email, send_type=send_type)

    base_url = settings.SITE_BASE_URL.rstrip("/")

    if send_type == "register":
        title = "问渠在线激活链接"
        body = f"请点击下面的链接激活你的帐号:{base_url}/active/{code}"
    elif send_type == "forget":
        title = "问渠在线密码重置链接"
        body = f"请点击下面的链接重置密码:{base_url}/reset/{code}"
    else:
        title = "问渠在线邮箱修改验证码"
        body = f"您的邮箱验证码为:{code}"

    send_mail(title, body, settings.DEFAULT_FROM_EMAIL, [email])
