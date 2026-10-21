from courses.models import Course
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic.base import View
from operation.models import UserCourse, UserFavorite, UserMessage
from organization.models import CourseOrg, Teacher
from utils.email_send import send_register_email
from utils.pagination import paginate

from .forms import (
    ForgetForm,
    LoginForm,
    ModifyPwdForm,
    RegisterForm,
    UpdatePwdForm,
    UploadImageForm,
    UserInfoForm,
)
from .models import VERIFY_CODES, Banner, EmailVerifyRecord, UserProfile

MESSAGE_PAGE_SIZE = 5


class LoginView(View):
    """
    用户登录
    """

    def get(self, request):
        return render(request, "login.html", {"next": request.GET.get("next", "")})

    def post(self, request):
        context = {"next": request.POST.get("next", "")}
        login_form = LoginForm(request.POST)
        if not login_form.is_valid():
            return render(
                request, "login.html", {**context, "login_form": login_form}
            )

        user_name = login_form.cleaned_data["username"]
        pass_word = login_form.cleaned_data["password"]
        user = authenticate(request, username=user_name, password=pass_word)

        if user is None:
            return render(
                request,
                "login.html",
                {**context, "login_form": login_form, "msg": "用户或密码错误！"},
            )
        if not user.is_active:
            if user.email:
                send_register_email(user.email, send_type="register")
            return render(
                request,
                "login.html",
                {**context, "login_form": login_form, "msg": "用户未激活！"},
            )

        login(request, user)
        return HttpResponseRedirect(self.redirect_to(request))

    @staticmethod
    def redirect_to(request):
        """登录后回到 LoginRequiredMixin 记下的目标页，只接受本站地址。"""
        next_url = request.POST.get("next") or request.GET.get("next") or ""
        if url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return next_url
        return reverse("index")


class ActiveUserView(View):
    """
    注册用户邮件链接
    """

    def get(self, request, active_code):
        record = EmailVerifyRecord.usable(
            code=active_code, send_type="register"
        ).first()
        user = (
            UserProfile.objects.filter(email=record.email).first() if record else None
        )
        if user is None:
            return render(request, "active_fail.html", {})

        # 消费验证码和激活用户必须同生同死，否则半途失败会让链接彻底失效
        with transaction.atomic():
            record.delete()
            user.is_active = True
            user.save(update_fields=["is_active"])
        return render(request, "login.html", {"msg": "激活成功，请登录！"})


class RegisterView(View):
    """
    注册用户
    """

    def get(self, request):
        return render(request, "register.html", {"register_form": RegisterForm()})

    def post(self, request):
        register_form = RegisterForm(request.POST)
        if not register_form.is_valid():
            return render(request, "register.html", {"register_form": register_form})

        user_name = register_form.cleaned_data["username"]
        email = register_form.cleaned_data["email"]

        if UserProfile.objects.filter(username=user_name).exists():
            return render(
                request,
                "register.html",
                {"register_form": register_form, "msg": "该用户名已被注册"},
            )
        if UserProfile.objects.filter(email=email).exists():
            return render(
                request,
                "register.html",
                {"register_form": register_form, "msg": "该邮箱已被注册"},
            )

        user_profile = UserProfile(username=user_name, email=email, is_active=False)
        user_profile.set_password(register_form.cleaned_data["password"])

        # 用户和欢迎消息一起落库，别出现没激活也没消息的半截用户
        with transaction.atomic():
            user_profile.save()
            UserMessage.objects.create(
                user=user_profile.id, message="欢迎注册问渠在线"
            )

        send_register_email(email, send_type="register")
        return render(
            request,
            "login.html",
            {"msg": f"注册成功，激活邮件已发送到 {email}"},
        )


class ForgetPwdView(View):
    """
    忘记密码
    """

    def get(self, request):
        return render(request, "forgetpwd.html", {"forget_form": ForgetForm()})

    def post(self, request):
        forget_form = ForgetForm(request.POST)
        if not forget_form.is_valid():
            return render(request, "forgetpwd.html", {"forget_form": forget_form})

        # 无论邮箱是否注册过都回同一句话，避免暴露已注册邮箱
        send_register_email(forget_form.cleaned_data["email"], send_type="forget")
        return render(request, "send_success.html", {})


class ResetView(View):
    """
    修改密码邮件链接
    """

    def get(self, request, active_code):
        record = EmailVerifyRecord.usable(code=active_code, send_type="forget").first()
        if record is None:
            return render(request, "active_fail.html", {})

        # 把待重置的邮箱绑定到会话，后续提交不再信任表单里传来的邮箱
        # 会话只能存纯 JSON 标量，这里记时间戳而不是 datetime
        request.session["reset_email"] = record.email
        request.session["reset_email_at"] = timezone.now().timestamp()
        return render(request, "password_reset.html", {"email": record.email})


class ModifyPwdView(View):
    """
    修改用户密码
    """

    def post(self, request):
        email = request.session.get("reset_email", "")
        armed_at = request.session.get("reset_email_at")
        # 点过一次链接不算永久授权：绑定邮箱的会话窗口和验证码本身一样只有一期 TTL
        ttl = VERIFY_CODES["forget"]["ttl"]
        if not email or armed_at is None:
            return render(request, "active_fail.html", {})
        if timezone.now().timestamp() - armed_at > ttl.total_seconds():
            return render(request, "active_fail.html", {})

        user = UserProfile.objects.filter(email=email).first()
        if user is None:
            return render(request, "active_fail.html", {})

        modify_form = ModifyPwdForm(request.POST)
        if not modify_form.is_valid():
            return render(
                request,
                "password_reset.html",
                {"email": email, "modify_form": modify_form},
            )

        if (
            modify_form.cleaned_data["password1"]
            != modify_form.cleaned_data["password2"]
        ):
            return render(
                request, "password_reset.html", {"email": email, "msg": "密码不一致"}
            )

        user.set_password(modify_form.cleaned_data["password1"])
        # 重置链接一次有效，连同该邮箱其他未使用的 forget 验证码一起作废
        with transaction.atomic():
            user.save(update_fields=["password"])
            EmailVerifyRecord.objects.filter(email=email, send_type="forget").delete()
        del request.session["reset_email"]
        return render(request, "login.html", {"msg": "密码修改成功，请登录！"})


class LogOutView(View):
    """
    用户登出
    """

    def get(self, request):
        logout(request)
        return HttpResponseRedirect(reverse("login"))


class UserInfoView(LoginRequiredMixin, View):
    """
    用户个人信息
    """

    def get(self, request):
        return render(request, "usercenter-info.html", {"sort": "info"})

    def post(self, request):
        user_info_form = UserInfoForm(request.POST, instance=request.user)
        if user_info_form.is_valid():
            user_info_form.save()
            return JsonResponse({"status": "success"})
        return JsonResponse(user_info_form.errors)


class UploadImageView(LoginRequiredMixin, View):
    """
    用户修改头像
    """

    def post(self, request):
        image_form = UploadImageForm(request.POST, request.FILES, instance=request.user)
        if image_form.is_valid():
            image_form.save()
            return JsonResponse({"status": "success"})
        return JsonResponse({"status": "fail"})


class UpdatePwdView(LoginRequiredMixin, View):
    """
    在个人中心修改用户密码
    """

    def post(self, request):
        modify_form = UpdatePwdForm(request.user, request.POST)
        if not modify_form.is_valid():
            return JsonResponse(modify_form.errors)

        if (
            modify_form.cleaned_data["password1"]
            != modify_form.cleaned_data["password2"]
        ):
            return JsonResponse({"status": "fail", "msg": "密码不一致"})

        request.user.set_password(modify_form.cleaned_data["password1"])
        request.user.save(update_fields=["password"])
        return JsonResponse({"status": "success"})


class SendEmailView(LoginRequiredMixin, View):
    """
    发送验证码修改邮箱
    """

    def post(self, request):
        email = request.POST.get("email", "")
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({"email": "邮箱格式不正确"})

        if UserProfile.objects.filter(email=email).exists():
            return JsonResponse({"email": "邮箱已经存在"})

        send_register_email(email, "update_email")
        return JsonResponse({"status": "success"})


class UpdateEmailView(LoginRequiredMixin, View):
    """
    修改用户邮箱
    """

    def post(self, request):
        email = request.POST.get("email", "")
        code = request.POST.get("code", "")

        record = EmailVerifyRecord.usable(
            email=email, code=code, send_type="update_email"
        ).first()
        if record is None:
            return JsonResponse({"email": "验证码出错"})
        if UserProfile.objects.filter(email=email).exists():
            return JsonResponse({"email": "邮箱已经存在"})

        # 验证码一次有效
        with transaction.atomic():
            record.delete()
            request.user.email = email
            request.user.save(update_fields=["email"])
        return JsonResponse({"status": "success"})


class MyCourseView(LoginRequiredMixin, View):
    """
    我的课程
    """

    def get(self, request):
        user_courses = (
            UserCourse.objects.filter(user=request.user)
            .select_related("course", "course__course_org")
            .order_by("-add_time")
        )
        return render(
            request,
            "usercenter-mycourse.html",
            {
                "user_courses": user_courses,
                "sort": "course",
            },
        )


class MyFavOrgView(LoginRequiredMixin, View):
    """
    我收藏的课程机构
    """

    def get(self, request):
        fav_ids = UserFavorite.objects.filter(
            user=request.user, fav_type=UserFavorite.ORG
        ).values_list("fav_id", flat=True)
        return render(
            request,
            "usercenter-fav-org.html",
            {
                "org_list": CourseOrg.objects.filter(id__in=fav_ids)
                .select_related("city")
                .order_by("-add_time"),
                "sort": "fav_org",
            },
        )


class MyFavTeacherView(LoginRequiredMixin, View):
    """
    我收藏的教师
    """

    def get(self, request):
        fav_ids = UserFavorite.objects.filter(
            user=request.user, fav_type=UserFavorite.TEACHER
        ).values_list("fav_id", flat=True)
        return render(
            request,
            "usercenter-fav-teacher.html",
            {
                "teacher_list": Teacher.objects.filter(id__in=fav_ids)
                .select_related("org")
                .order_by("-add_time"),
                # 三个收藏页共用侧栏的「我的收藏」一项
                "sort": "fav_org",
            },
        )


class MyFavCourseView(LoginRequiredMixin, View):
    """
    我收藏的课程
    """

    def get(self, request):
        fav_ids = UserFavorite.objects.filter(
            user=request.user, fav_type=UserFavorite.COURSE
        ).values_list("fav_id", flat=True)
        return render(
            request,
            "usercenter-fav-course.html",
            {
                "course_list": Course.objects.filter(id__in=fav_ids)
                .select_related("course_org", "teacher")
                .order_by("-add_time"),
                "sort": "fav_org",
            },
        )


class MyMessageView(LoginRequiredMixin, View):
    """
    我的消息
    """

    def get(self, request):
        all_messages = UserMessage.objects.filter(user=request.user.id).order_by(
            "-add_time"
        )

        # 用户进入个人中心后清空未读消息的记录
        UserMessage.objects.filter(user=request.user.id, has_read=False).update(
            has_read=True
        )

        return render(
            request,
            "usercenter-message.html",
            {
                "messages": paginate(request, all_messages, MESSAGE_PAGE_SIZE),
                "sort": "message",
            },
        )


class IndexView(View):
    """
    问渠在线首页
    """

    def get(self, request):
        courses = Course.objects.select_related("course_org", "teacher")
        return render(
            request,
            "index.html",
            {
                # 轮播图 index 常取默认值，同一序号靠 id 定序，否则顺序会随机翻
                "all_banners": Banner.objects.order_by("index", "id"),
                # 排序字段必须写死，否则换数据库后首页卡片顺序会变
                "courses": courses.filter(is_banner=False).order_by("-click_nums")[:6],
                "banner_courses": courses.filter(is_banner=True).order_by(
                    "-click_nums"
                )[:3],
                "course_orgs": CourseOrg.objects.select_related("city").order_by(
                    "-click_num"
                )[:15],
            },
        )


def render_error(request, template, status_code):
    """错误页要带正确的状态码，直接用 render 会回 200。"""
    response = render(request, template, {})
    response.status_code = status_code
    return response


def page_not_found(request, exception):
    """全局 404 页，签名里的 exception 由 Django 传入。"""
    return render_error(request, "404.html", 404)


def page_error(request):
    """全局 500 页。"""
    return render_error(request, "500.html", 500)


def permission_denied(request, exception):
    """全局 403 页。"""
    return render_error(request, "403.html", 403)
