from captcha.fields import CaptchaField
from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import UserProfile


def clean_strong_password(password):
    """套用 settings 里的 AUTH_PASSWORD_VALIDATORS，而不只依赖表单的 min_length。"""
    try:
        validate_password(password)
    except ValidationError as error:
        raise forms.ValidationError(error.messages[0]) from error
    return password


class LoginForm(forms.Form):
    """登录表单。"""

    username = forms.CharField(required=True)
    password = forms.CharField(required=True, min_length=5)


class RegisterForm(forms.Form):
    """注册表单，邮箱验证码防止批量注册。"""

    username = forms.CharField(required=True)
    email = forms.EmailField(required=True)
    password = forms.CharField(required=True, min_length=8)
    captcha = CaptchaField(error_messages={"invalid": "验证码错误"})

    def clean_password(self):
        return clean_strong_password(self.cleaned_data["password"])


class ForgetForm(forms.Form):
    """找回密码第一步：按邮箱发验证码。"""

    email = forms.EmailField(required=True)
    captcha = CaptchaField(error_messages={"invalid": "验证码错误"})


class ModifyPwdForm(forms.Form):
    """新密码表单，两次输入是否一致由提交它的视图判断。"""

    password1 = forms.CharField(required=True, min_length=8)
    password2 = forms.CharField(required=True, min_length=8)

    def clean_password1(self):
        return clean_strong_password(self.cleaned_data["password1"])


class UpdatePwdForm(ModifyPwdForm):
    """个人中心改密码：要先验当前密码，不然拿到一个未过期的会话就能改走账号。"""

    old_password = forms.CharField(required=True, label="原密码")

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_old_password(self):
        old_password = self.cleaned_data["old_password"]
        if not self.user.check_password(old_password):
            raise forms.ValidationError("原密码不正确")
        return old_password


class UserInfoForm(forms.ModelForm):
    """个人资料表单。"""

    class Meta:
        model = UserProfile
        fields = ["nick_name", "gender", "birday", "address", "mobile"]


class UploadImageForm(forms.ModelForm):
    """头像上传表单。"""

    class Meta:
        model = UserProfile
        fields = ["image"]
