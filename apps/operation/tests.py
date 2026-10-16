from django.test import TestCase
from django.urls import reverse
from operation.models import (
    CourseComments,
    UserAsk,
    UserCourse,
    UserFavorite,
    UserMessage,
)
from utils.testing import make_course, make_superuser, make_user


class OperationModelTests(TestCase):
    def test_string_representations(self):
        user = make_user(username="xiaoming")
        course = make_course(name="Django 实战")

        ask = UserAsk.objects.create(
            name="小李", mobile="13800138000", course_name="Django"
        )
        comment = CourseComments.objects.create(
            user=user, course=course, comments="讲得清楚"
        )
        favorite = UserFavorite.objects.create(user=user, fav_id=course.id, fav_type=1)
        message = UserMessage.objects.create(user=user.id, message="课程已上线")
        learned = UserCourse.objects.create(user=user, course=course)

        self.assertEqual(str(ask), "小李 咨询 Django")
        self.assertEqual(str(comment), "xiaoming 评论 Django 实战")
        self.assertEqual(str(favorite), "xiaoming 收藏 课程")
        # UserMessage.user 是整数 id 而非外键，展示时只能给出 id
        self.assertEqual(str(message), f"{user.id}: 课程已上线")
        self.assertEqual(str(learned), "xiaoming 学习 Django 实战")

    def test_long_message_is_truncated_in_display(self):
        message = UserMessage.objects.create(user=1, message="长" * 30)

        self.assertEqual(str(message), "1: " + "长" * 20)

    def test_removing_a_course_clears_its_courses_and_comments(self):
        user = make_user()
        course = make_course()
        CourseComments.objects.create(user=user, course=course, comments="评论")
        UserCourse.objects.create(user=user, course=course)

        course.delete()

        self.assertEqual(CourseComments.objects.count(), 0)
        self.assertEqual(UserCourse.objects.count(), 0)

    def test_removing_a_user_clears_their_records(self):
        user = make_user()
        course = make_course()
        CourseComments.objects.create(user=user, course=course, comments="评论")
        UserCourse.objects.create(user=user, course=course)
        UserFavorite.objects.create(user=user, fav_id=course.id, fav_type=1)
        UserMessage.objects.create(user=user.id, message="消息")

        user.delete()

        self.assertEqual(CourseComments.objects.count(), 0)
        self.assertEqual(UserCourse.objects.count(), 0)
        self.assertEqual(UserFavorite.objects.count(), 0)
        self.assertEqual(UserMessage.objects.count(), 1)


class OperationAdminTests(TestCase):
    def setUp(self):
        self.client.force_login(make_superuser())

    def test_admin_pages_render(self):
        user = make_user()
        course = make_course()
        UserAsk.objects.create(name="小李", mobile="13800138000", course_name="Django")
        CourseComments.objects.create(user=user, course=course, comments="好课")
        UserFavorite.objects.create(user=user, fav_id=course.id, fav_type=1)
        UserMessage.objects.create(user=user.id, message="欢迎")
        UserCourse.objects.create(user=user, course=course)

        urls = [
            reverse("admin:operation_userask_changelist"),
            reverse("admin:operation_coursecomments_changelist"),
            reverse("admin:operation_userfavorite_changelist"),
            reverse("admin:operation_usermessage_changelist"),
            reverse("admin:operation_usercourse_changelist"),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
