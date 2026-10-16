from django.contrib.auth import authenticate
from django.core import mail
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone
from operation.models import UserFavorite, UserMessage
from users.models import Banner, EmailVerifyRecord, UserProfile
from utils.testing import make_course, make_org, make_superuser, make_user

# CAPTCHA_TEST_MODE 打开时填 passed 即可通过验证码校验
CAPTCHA_OK = {"captcha_0": "test-hashkey", "captcha_1": "passed"}
REGISTER_DATA = {
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "newpass123",
}


class CustomBackendTests(TestCase):
    def setUp(self):
        self.user = make_user(
            username="xiaoming", email="xiaoming@example.com", password="oldpass123"
        )

    def test_authenticates_by_username_and_email(self):
        request = RequestFactory().post(reverse("login"))
        self.assertEqual(
            authenticate(request, username="xiaoming", password="oldpass123"), self.user
        )
        self.assertEqual(
            authenticate(
                request, username="xiaoming@example.com", password="oldpass123"
            ),
            self.user,
        )

    def test_rejects_wrong_password(self):
        self.assertIsNone(
            authenticate(None, username="xiaoming", password="badpass123")
        )

    def test_ignores_unknown_username(self):
        self.assertIsNone(authenticate(None, username="ghost", password="oldpass123"))

    def test_identifier_shared_by_two_accounts(self):
        # 甲的邮箱正好是乙的用户名时，两个账号都要能登录
        other = make_user(
            username="xiaoming@example.com",
            email="other@example.com",
            password="otherpass123",
        )
        request = RequestFactory().post(reverse("login"))

        self.assertEqual(
            authenticate(
                request, username="xiaoming@example.com", password="oldpass123"
            ),
            self.user,
        )
        self.assertEqual(
            authenticate(
                request, username="xiaoming@example.com", password="otherpass123"
            ),
            other,
        )


class LoginViewTests(TestCase):
    def setUp(self):
        self.user = make_user(
            username="xiaoming", email="xiaoming@example.com", password="oldpass123"
        )

    def test_login_redirects_to_index(self):
        response = self.client.post(
            reverse("login"), {"username": "xiaoming", "password": "oldpass123"}
        )
        self.assertRedirects(response, reverse("index"), fetch_redirect_response=False)

    def test_login_with_email(self):
        response = self.client.post(
            reverse("login"),
            {"username": "xiaoming@example.com", "password": "oldpass123"},
        )
        self.assertRedirects(response, reverse("index"), fetch_redirect_response=False)

    def test_wrong_password_shows_error(self):
        response = self.client.post(
            reverse("login"), {"username": "xiaoming", "password": "badpass123"}
        )
        self.assertTemplateUsed(response, "login.html")
        self.assertEqual(response.context["msg"], "用户或密码错误！")

    def test_short_password_is_rejected_by_form(self):
        response = self.client.post(
            reverse("login"), {"username": "xiaoming", "password": "123"}
        )
        self.assertIn("password", response.context["login_form"].errors)

    def test_inactive_user_cannot_login_and_gets_new_activation_mail(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])

        response = self.client.post(
            reverse("login"), {"username": "xiaoming", "password": "oldpass123"}
        )

        self.assertEqual(response.context["msg"], "用户未激活！")
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["xiaoming@example.com"])

    def test_login_returns_to_the_page_that_needed_login(self):
        response = self.client.post(
            reverse("login"),
            {
                "username": "xiaoming",
                "password": "oldpass123",
                "next": reverse("users:mymessage"),
            },
        )

        self.assertRedirects(response, reverse("users:mymessage"))

    def test_login_ignores_a_foreign_next_url(self):
        response = self.client.post(
            reverse("login"),
            {
                "username": "xiaoming",
                "password": "oldpass123",
                "next": "http://evil.example.com/steal",
            },
        )

        self.assertRedirects(response, reverse("index"), fetch_redirect_response=False)

    def test_inactive_user_without_email_gets_no_mail(self):
        self.user.email = ""
        self.user.is_active = False
        self.user.save(update_fields=["email", "is_active"])

        response = self.client.post(
            reverse("login"), {"username": "xiaoming", "password": "oldpass123"}
        )

        self.assertEqual(response.context["msg"], "用户未激活！")
        self.assertEqual(len(mail.outbox), 0)


class RegisterViewTests(TestCase):
    def test_valid_register_creates_inactive_user(self):
        response = self.client.post(
            reverse("register"), {**REGISTER_DATA, **CAPTCHA_OK}
        )

        user = UserProfile.objects.get(username="newuser")
        self.assertTemplateUsed(response, "login.html")
        self.assertFalse(user.is_active)
        self.assertTrue(user.check_password("newpass123"))
        self.assertEqual(
            EmailVerifyRecord.objects.filter(
                email="newuser@example.com", send_type="register"
            ).count(),
            1,
        )
        self.assertEqual(UserMessage.objects.filter(user=user.id).count(), 1)

    def test_duplicate_username_is_rejected(self):
        make_user(username="newuser", email="other@example.com")

        response = self.client.post(
            reverse("register"), {**REGISTER_DATA, **CAPTCHA_OK}
        )

        self.assertEqual(response.context["msg"], "该用户名已被注册")
        self.assertEqual(UserProfile.objects.filter(username="newuser").count(), 1)

    def test_duplicate_email_is_rejected(self):
        make_user(username="other", email="newuser@example.com")

        response = self.client.post(
            reverse("register"), {**REGISTER_DATA, **CAPTCHA_OK}
        )

        self.assertEqual(response.context["msg"], "该邮箱已被注册")

    def test_wrong_captcha_is_rejected(self):
        response = self.client.post(
            reverse("register"),
            {**REGISTER_DATA, "captcha_0": "k", "captcha_1": "nope"},
        )

        self.assertFalse(UserProfile.objects.filter(username="newuser").exists())
        self.assertIn("captcha", response.context["register_form"].errors)

    def test_numeric_password_is_rejected(self):
        response = self.client.post(
            reverse("register"),
            {**REGISTER_DATA, "password": "12345678", **CAPTCHA_OK},
        )

        self.assertFalse(UserProfile.objects.filter(username="newuser").exists())
        self.assertIn("password", response.context["register_form"].errors)


class ActiveUserViewTests(TestCase):
    def setUp(self):
        self.user = make_user(
            username="xiaoming", email="xiaoming@example.com", is_active=False
        )
        EmailVerifyRecord.objects.create(
            code="active-code", email="xiaoming@example.com", send_type="register"
        )

    def test_valid_code_activates_user(self):
        self.client.get(reverse("user_active", args=["active-code"]))

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_unknown_code_shows_failure(self):
        response = self.client.get(reverse("user_active", args=["nope"]))

        self.assertTemplateUsed(response, "active_fail.html")

    def test_code_for_missing_email_shows_failure(self):
        self.user.delete()

        response = self.client.get(reverse("user_active", args=["active-code"]))

        self.assertTemplateUsed(response, "active_fail.html")

    def test_activation_code_works_only_once(self):
        self.client.get(reverse("user_active", args=["active-code"]))

        response = self.client.get(reverse("user_active", args=["active-code"]))

        self.assertTemplateUsed(response, "active_fail.html")
        self.assertFalse(EmailVerifyRecord.objects.exists())

    def test_expired_activation_code_is_rejected(self):
        EmailVerifyRecord.objects.update(
            send_time=timezone.now() - timezone.timedelta(days=2)
        )

        response = self.client.get(reverse("user_active", args=["active-code"]))

        self.assertTemplateUsed(response, "active_fail.html")
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)


class PasswordResetTests(TestCase):
    def setUp(self):
        self.user = make_user(
            username="xiaoming", email="xiaoming@example.com", password="oldpass123"
        )
        EmailVerifyRecord.objects.create(
            code="reset-code", email="xiaoming@example.com", send_type="forget"
        )

    def test_forget_page_mails_the_submitted_address(self):
        response = self.client.post(
            reverse("forget_pwd"), {"email": "someone@else.com", **CAPTCHA_OK}
        )

        self.assertTemplateUsed(response, "send_success.html")
        self.assertEqual(mail.outbox[0].to, ["someone@else.com"])
        self.assertEqual(
            EmailVerifyRecord.objects.filter(
                email="someone@else.com", send_type="forget"
            ).count(),
            1,
        )

    def test_reset_link_stores_email_in_session(self):
        response = self.client.get(reverse("reset_pwd", args=["reset-code"]))

        self.assertTemplateUsed(response, "password_reset.html")
        self.assertEqual(self.client.session["reset_email"], "xiaoming@example.com")

    def test_reset_link_with_unknown_code_shows_failure(self):
        response = self.client.get(reverse("reset_pwd", args=["wrong"]))

        self.assertTemplateUsed(response, "active_fail.html")
        self.assertNotIn("reset_email", self.client.session)

    def test_reset_link_session_window_expires(self):
        self.client.get(reverse("reset_pwd", args=["reset-code"]))
        session = self.client.session
        session["reset_email_at"] = (
            timezone.now() - timezone.timedelta(hours=25)
        ).timestamp()
        session.save()

        response = self.client.post(
            reverse("modify_pwd"),
            {"password1": "newpass123", "password2": "newpass123"},
        )

        self.assertTemplateUsed(response, "active_fail.html")
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("oldpass123"))

    def test_password_can_only_be_changed_after_the_link(self):
        response = self.client.post(
            reverse("modify_pwd"),
            {"password1": "newpass123", "password2": "newpass123"},
        )

        self.assertTemplateUsed(response, "active_fail.html")
        self.assertTrue(self.user.check_password("oldpass123"))

    def test_modify_password_uses_session_email_not_post_data(self):
        victim = make_user(
            username="other", email="other@example.com", password="victimpass123"
        )
        self.client.get(reverse("reset_pwd", args=["reset-code"]))

        response = self.client.post(
            reverse("modify_pwd"),
            {
                "email": "other@example.com",
                "password1": "newpass123",
                "password2": "newpass123",
            },
        )

        self.assertTemplateUsed(response, "login.html")
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpass123"))
        self.assertTrue(victim.check_password("victimpass123"))
        self.assertNotIn("reset_email", self.client.session)

    def test_mismatched_passwords_are_rejected(self):
        self.client.get(reverse("reset_pwd", args=["reset-code"]))

        response = self.client.post(
            reverse("modify_pwd"),
            {"password1": "newpass123", "password2": "otherpass123"},
        )

        self.assertEqual(response.context["msg"], "密码不一致")
        self.assertTrue(self.user.check_password("oldpass123"))

    def test_reset_link_works_only_once(self):
        self.client.get(reverse("reset_pwd", args=["reset-code"]))
        self.client.post(
            reverse("modify_pwd"),
            {"password1": "newpass123", "password2": "newpass123"},
        )

        response = self.client.get(reverse("reset_pwd", args=["reset-code"]))

        self.assertTemplateUsed(response, "active_fail.html")
        self.assertFalse(EmailVerifyRecord.objects.exists())

    def test_expired_reset_code_is_rejected(self):
        EmailVerifyRecord.objects.update(
            send_time=timezone.now() - timezone.timedelta(days=2)
        )

        response = self.client.get(reverse("reset_pwd", args=["reset-code"]))

        self.assertTemplateUsed(response, "active_fail.html")
        self.assertNotIn("reset_email", self.client.session)

    def test_weak_new_password_is_rejected(self):
        self.client.get(reverse("reset_pwd", args=["reset-code"]))

        response = self.client.post(
            reverse("modify_pwd"),
            {"password1": "12345678", "password2": "12345678"},
        )

        self.assertIn("password1", response.context["modify_form"].errors)
        self.assertTrue(self.user.check_password("oldpass123"))
        self.assertEqual(EmailVerifyRecord.objects.count(), 1)


class AccountSettingsTests(TestCase):
    def setUp(self):
        self.user = make_user(
            username="xiaoming", email="xiaoming@example.com", password="oldpass123"
        )
        self.client.force_login(self.user)

    def test_anonymous_users_are_redirected_to_login(self):
        self.client.logout()

        response = self.client.get(reverse("users:mymessage"))

        self.assertRedirects(
            response,
            f'{reverse("login")}?next={reverse("users:mymessage")}',
            fetch_redirect_response=False,
        )

    def test_profile_page_renders(self):
        response = self.client.get(reverse("users:user_info"))

        self.assertTemplateUsed(response, "usercenter-info.html")

    def test_profile_is_updated(self):
        response = self.client.post(
            reverse("users:user_info"),
            {
                "nick_name": "小明",
                "gender": "male",
                "birday": "1990-01-01",
                "address": "广州",
                "mobile": "13800138000",
            },
        )

        self.assertEqual(response.json(), {"status": "success"})
        self.user.refresh_from_db()
        self.assertEqual(self.user.nick_name, "小明")
        self.assertEqual(self.user.mobile, "13800138000")

    def test_too_long_mobile_returns_field_errors(self):
        response = self.client.post(
            reverse("users:user_info"),
            {
                "nick_name": "小明",
                "gender": "male",
                "address": "广州",
                "mobile": "1" * 12,
            },
        )

        self.assertIn("mobile", response.json())

    def test_change_password_from_usercenter(self):
        response = self.client.post(
            reverse("users:update_pwd"),
            {
                "old_password": "oldpass123",
                "password1": "newpass123",
                "password2": "newpass123",
            },
        )

        self.assertEqual(response.json(), {"status": "success"})
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpass123"))

    def test_change_password_requires_correct_old_password(self):
        response = self.client.post(
            reverse("users:update_pwd"),
            {
                "old_password": "wrongpass123",
                "password1": "newpass123",
                "password2": "newpass123",
            },
        )

        self.assertIn("old_password", response.json())
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("oldpass123"))

    def test_change_password_rejects_mismatch(self):
        response = self.client.post(
            reverse("users:update_pwd"),
            {
                "old_password": "oldpass123",
                "password1": "newpass123",
                "password2": "otherpass123",
            },
        )

        self.assertEqual(response.json()["msg"], "密码不一致")

    def test_send_email_code_for_new_address(self):
        response = self.client.post(
            reverse("users:sendemail_code"), {"email": "fresh@example.com"}
        )

        self.assertEqual(response.json(), {"status": "success"})
        record = EmailVerifyRecord.objects.get(send_type="update_email")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["fresh@example.com"])

        update = self.client.post(
            reverse("users:update_email"),
            {"email": "fresh@example.com", "code": record.code},
        )
        self.assertEqual(update.json(), {"status": "success"})
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "fresh@example.com")
        self.assertFalse(EmailVerifyRecord.objects.filter(id=record.id).exists())

    def test_send_email_code_rejects_taken_address(self):
        make_user(username="other", email="taken@example.com")

        response = self.client.post(
            reverse("users:sendemail_code"), {"email": "taken@example.com"}
        )

        self.assertEqual(response.json()["email"], "邮箱已经存在")

    def test_send_email_code_rejects_bad_format(self):
        response = self.client.post(
            reverse("users:sendemail_code"), {"email": "not-an-email"}
        )

        self.assertEqual(response.json()["email"], "邮箱格式不正确")

    def test_update_email_rejects_wrong_code(self):
        response = self.client.post(
            reverse("users:update_email"),
            {"email": "fresh@example.com", "code": "0000"},
        )

        self.assertEqual(response.json()["email"], "验证码出错")

    def test_change_password_rejects_weak_password(self):
        response = self.client.post(
            reverse("users:update_pwd"),
            {
                "old_password": "oldpass123",
                "password1": "12345678",
                "password2": "12345678",
            },
        )

        self.assertIn("password1", response.json())
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("oldpass123"))

    def test_email_code_expires(self):
        record = EmailVerifyRecord.objects.create(
            email="fresh@example.com", code="1234", send_type="update_email"
        )
        record.send_time = timezone.now() - timezone.timedelta(minutes=11)
        record.save(update_fields=["send_time"])

        response = self.client.post(
            reverse("users:update_email"),
            {"email": "fresh@example.com", "code": record.code},
        )

        self.assertEqual(response.json()["email"], "验证码出错")
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "xiaoming@example.com")


class MessageAndFavoriteTests(TestCase):
    def setUp(self):
        self.user = make_user(username="xiaoming", email="xiaoming@example.com")
        self.client.force_login(self.user)

    def test_unread_message_count(self):
        UserMessage.objects.create(user=self.user.id, message="第一条")
        UserMessage.objects.create(user=self.user.id, message="第二条")
        UserMessage.objects.create(user=self.user.id, message="已读", has_read=True)

        self.assertEqual(self.user.unread_message_nums(), 2)

    def test_message_page_marks_all_read_and_paginates(self):
        for index in range(6):
            UserMessage.objects.create(
                user=self.user.id, message=f"消息 {index}"
            )

        response = self.client.get(reverse("users:mymessage"))

        self.assertEqual(len(response.context["messages"].object_list), 5)
        self.assertEqual(response.context["messages"].paginator.num_pages, 2)
        self.assertEqual(
            UserMessage.objects.filter(user=self.user.id, has_read=False).count(), 0
        )

    def test_favorite_pages_ignore_deleted_objects(self):
        course = make_course(name="已删除的课程")
        org = make_org(name="待删除的机构")
        UserFavorite.objects.create(user=self.user, fav_id=course.id, fav_type=1)
        UserFavorite.objects.create(user=self.user, fav_id=org.id, fav_type=2)

        course.delete()
        org.delete()

        for url_name in (
            "users:myfav_course",
            "users:myfav_org",
            "users:myfav_teacher",
        ):
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 200)


class IndexViewTests(TestCase):
    def setUp(self):
        self.org = make_org()

    def test_index_separates_banner_courses(self):
        make_course(name="普通课程", org=self.org)
        make_course(name="轮播课程", org=self.org, is_banner=True)
        Banner.objects.create(
            title="快", image="banner/fast.png", url="https://example.com", index=200
        )
        Banner.objects.create(
            title="慢", image="banner/slow.png", url="https://example.com", index=100
        )

        response = self.client.get(reverse("index"))

        self.assertEqual(
            [b.title for b in response.context["all_banners"]], ["慢", "快"]
        )
        self.assertEqual([c.name for c in response.context["courses"]], ["普通课程"])
        self.assertEqual(
            [c.name for c in response.context["banner_courses"]], ["轮播课程"]
        )

    def test_unknown_url_uses_custom_404(self):
        response = self.client.get("/no-such-page/")

        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "404.html")


class UserAdminTests(TestCase):
    def setUp(self):
        self.client.force_login(make_superuser())

    def test_staff_without_permission_gets_403_page(self):
        self.client.force_login(
            make_user(username="staffonly", email="staff@example.com", is_staff=True)
        )

        response = self.client.get(reverse("admin:courses_course_changelist"))

        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "403.html")

    def test_user_related_pages_render(self):
        user = make_user(username="xiaoming", email="xiaoming@example.com")
        EmailVerifyRecord.objects.create(
            code="c1", email=user.email, send_type="register"
        )
        Banner.objects.create(
            title="轮播", image="banner/a.png", url="https://example.com"
        )

        urls = [
            reverse("admin:index"),
            reverse("admin:users_userprofile_changelist"),
            reverse("admin:users_userprofile_add"),
            reverse("admin:users_userprofile_change", args=[user.id]),
            reverse("admin:auth_group_changelist"),
            reverse("admin:users_emailverifyrecord_changelist"),
            reverse("admin:users_banner_changelist"),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
