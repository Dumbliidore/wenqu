from courses.admin import BannerCourseAdmin, CourseAdmin
from courses.models import Course, CourseResource, Lesson, Video
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone
from operation.models import CourseComments, UserCourse
from utils.testing import make_course, make_org, make_superuser, make_teacher, make_user

from admin import admin_site

PAGE_SIZE = 6


def courses_page(response):
    return response.context["all_courses"]


class CourseModelTests(TestCase):
    def test_refresh_course_nums_counts_each_org_separately(self):
        org = make_org(name="机构 A")
        other_org = make_org(name="机构 B")
        for index in range(3):
            make_course(org=org, name=f"课程 {index}")
        make_course(org=other_org, name="另一家机构的课程")

        Course.objects.get(name="课程 0").refresh_course_nums()

        org.refresh_from_db()
        other_org.refresh_from_db()
        self.assertEqual(org.course_nums, 3)
        # 只重算本机构，其他机构的计数保持原值
        self.assertEqual(other_org.course_nums, 0)

    def test_go_to_links_to_course_detail(self):
        course = make_course()

        self.assertIn(reverse("course:course_detail", args=[course.id]), course.go_to())


class CourseListViewTests(TestCase):
    def setUp(self):
        self.org = make_org()
        self.teacher = make_teacher(self.org)
        now = timezone.now()
        for index in range(13):
            make_course(
                org=self.org,
                teacher=self.teacher,
                name=f"课程 {index}",
                desc=f"描述 {index}",
                detail=f"<p>详情 {index}</p>",
                students=index,
                click_nums=index,
                add_time=now - timezone.timedelta(days=index),
            )

    def test_default_order_and_pagination(self):
        response = self.client.get(reverse("course:course_list"))

        page = courses_page(response)
        self.assertEqual(page.paginator.num_pages, 3)
        self.assertEqual(
            [c.name for c in page.object_list], [f"课程 {i}" for i in range(PAGE_SIZE)]
        )

    def test_second_and_last_page(self):
        second = self.client.get(reverse("course:course_list"), {"page": 2})
        self.assertEqual(len(courses_page(second).object_list), PAGE_SIZE)

        overflow = self.client.get(reverse("course:course_list"), {"page": 99})
        self.assertEqual(courses_page(overflow).number, 3)
        self.assertEqual(len(courses_page(overflow).object_list), 1)

    def test_non_integer_page_falls_back_to_first(self):
        response = self.client.get(reverse("course:course_list"), {"page": "abc"})

        self.assertEqual(courses_page(response).number, 1)

    def test_search_covers_name_desc_and_detail(self):
        by_name = self.client.get(reverse("course:course_list"), {"keywords": "课程 3"})
        self.assertEqual([c.name for c in courses_page(by_name)], ["课程 3"])

        by_detail = self.client.get(
            reverse("course:course_list"), {"keywords": "详情 5"}
        )
        self.assertEqual([c.name for c in courses_page(by_detail)], ["课程 5"])

        by_desc = self.client.get(reverse("course:course_list"), {"keywords": "描述 6"})
        self.assertEqual([c.name for c in courses_page(by_desc)], ["课程 6"])

        nothing = self.client.get(
            reverse("course:course_list"), {"keywords": "不存在的关键词"}
        )
        self.assertEqual(len(courses_page(nothing)), 0)

    def test_sorting(self):
        hot = self.client.get(reverse("course:course_list"), {"sort": "hot"})
        self.assertEqual(
            [c.click_nums for c in courses_page(hot)], [12, 11, 10, 9, 8, 7]
        )

        students = self.client.get(reverse("course:course_list"), {"sort": "students"})
        self.assertEqual(
            [c.students for c in courses_page(students)], [12, 11, 10, 9, 8, 7]
        )

    def test_pagination_links_keep_sort_parameter(self):
        response = self.client.get(reverse("course:course_list"), {"sort": "hot"})

        self.assertIn("sort=hot&amp;page=2", response.content.decode("utf-8"))

    def test_hot_courses_side_list(self):
        response = self.client.get(reverse("course:course_list"))

        self.assertEqual(
            [c.name for c in response.context["hot_courses"]],
            ["课程 12", "课程 11", "课程 10"],
        )


class CourseDetailViewTests(TestCase):
    def setUp(self):
        self.course = make_course(name="Django 实战", tag="python")
        self.sibling = make_course(
            name="同标签课程", org=self.course.course_org, tag="python"
        )
        self.other_tag = make_course(
            name="无关课程", org=self.course.course_org, tag="go"
        )

    def test_detail_renders_rich_text_unescaped(self):
        response = self.client.get(
            reverse("course:course_detail", args=[self.course.id])
        )

        self.assertTemplateUsed(response, "course-detail.html")
        self.assertIn("<p>课程详情</p>", response.content.decode("utf-8"))

    def test_click_number_increases_once_per_visit(self):
        for _ in range(2):
            self.client.get(reverse("course:course_detail", args=[self.course.id]))

        self.course.refresh_from_db()
        self.assertEqual(self.course.click_nums, 2)

    def test_related_course_excludes_current_one(self):
        response = self.client.get(
            reverse("course:course_detail", args=[self.course.id])
        )

        self.assertEqual(
            [c.id for c in response.context["relate_courses"]], [self.sibling.id]
        )

    def test_untagged_course_has_no_related_list(self):
        plain = make_course(name="无标签课程", tag="")

        response = self.client.get(reverse("course:course_detail", args=[plain.id]))

        self.assertEqual(list(response.context["relate_courses"]), [])

    def test_authenticated_user_sees_favorite_state(self):
        user = make_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse("course:course_detail", args=[self.course.id])
        )
        self.assertFalse(response.context["has_fav_course"])
        self.assertFalse(response.context["has_fav_org"])

        self.client.post(
            reverse("org:add_fav"), {"fav_id": self.course.id, "fav_type": 1}
        )
        response = self.client.get(
            reverse("course:course_detail", args=[self.course.id])
        )
        self.assertTrue(response.context["has_fav_course"])
        self.assertFalse(response.context["has_fav_org"])

        self.client.post(
            reverse("org:add_fav"), {"fav_id": self.course.course_org_id, "fav_type": 2}
        )
        response = self.client.get(
            reverse("course:course_detail", args=[self.course.id])
        )
        self.assertTrue(response.context["has_fav_org"])

    def test_anonymous_user_has_no_favorite_state(self):
        response = self.client.get(
            reverse("course:course_detail", args=[self.course.id])
        )

        self.assertFalse(response.context["has_fav_course"])
        self.assertFalse(response.context["has_fav_org"])

    def test_missing_course_returns_404(self):
        response = self.client.get(reverse("course:course_detail", args=[999999]))

        self.assertEqual(response.status_code, 404)


class CourseInfoViewTests(TestCase):
    def setUp(self):
        self.course = make_course()
        self.lesson = Lesson.objects.create(course=self.course, name="第一章")
        Video.objects.create(lesson=self.lesson, name="第一节视频", learn_times=30)
        CourseResource.objects.create(
            course=self.course, name="课件", download="course/resource/notes.pdf"
        )

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(reverse("course:course_info", args=[self.course.id]))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_repeated_visits_enroll_and_count_once(self):
        self.client.force_login(make_user())

        for _ in range(2):
            response = self.client.get(
                reverse("course:course_info", args=[self.course.id])
            )
            self.assertTemplateUsed(response, "course-video.html")

        self.course.refresh_from_db()
        # 学习人数和学习关系都只在首次进入时记录
        self.assertEqual(self.course.students, 1)
        self.assertEqual(UserCourse.objects.filter(course=self.course).count(), 1)

    def test_popular_courses_come_from_other_learners(self):
        other = make_course(name="热门课程", org=self.course.course_org, click_nums=100)
        learner = make_user(username="learner")
        UserCourse.objects.create(user=learner, course=self.course)
        UserCourse.objects.create(user=learner, course=other)
        self.client.force_login(learner)

        response = self.client.get(reverse("course:course_info", args=[other.id]))

        self.assertEqual(
            [c.name for c in response.context["relate_courses"]], [self.course.name]
        )

    def test_no_recommended_courses_when_nobody_else_learned(self):
        self.client.force_login(make_user())

        response = self.client.get(reverse("course:course_info", args=[self.course.id]))

        self.assertEqual(list(response.context["relate_courses"]), [])


class CourseCommentViewTests(TestCase):
    def setUp(self):
        self.course = make_course(name="本课")
        self.other = make_course(name="别课", org=self.course.course_org)
        self.user = make_user()
        CourseComments.objects.create(
            course=self.other, comments="别课的评论", user=self.user
        )
        CourseComments.objects.create(
            course=self.course,
            comments="较早",
            user=self.user,
            add_time=timezone.now() - timezone.timedelta(days=1),
        )
        CourseComments.objects.create(
            course=self.course, comments="较新", user=self.user
        )

    def test_only_current_course_comments_are_listed(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("course:course_comment", args=[self.course.id])
        )

        self.assertEqual(
            [c.comments for c in response.context["all_comments"]], ["较新", "较早"]
        )

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(
            reverse("course:course_comment", args=[self.course.id])
        )

        self.assertEqual(response.status_code, 302)


class AddCommentViewTests(TestCase):
    def setUp(self):
        self.course = make_course()
        self.user = make_user()

    def test_anonymous_user_cannot_comment(self):
        response = self.client.post(
            reverse("course:add_comment"),
            {"course_id": self.course.id, "comments": "hi"},
        )

        self.assertEqual(response.json(), {"status": "fail", "msg": "用户未登录"})

    def test_valid_comment_is_saved(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("course:add_comment"),
            {"course_id": self.course.id, "comments": "讲得好"},
        )

        self.assertEqual(response.json(), {"status": "success", "msg": "添加成功"})
        self.assertEqual(
            CourseComments.objects.filter(course=self.course, user=self.user).count(), 1
        )

    def test_empty_comment_is_rejected(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("course:add_comment"), {"course_id": self.course.id, "comments": ""}
        )

        self.assertEqual(response.json()["status"], "fail")
        self.assertEqual(CourseComments.objects.count(), 0)

    def test_bad_course_id_is_rejected(self):
        self.client.force_login(self.user)

        for course_id in ("", "abc", "0"):
            with self.subTest(course_id=course_id):
                response = self.client.post(
                    reverse("course:add_comment"),
                    {"course_id": course_id, "comments": "x"},
                )
                self.assertEqual(response.json()["status"], "fail")

    def test_absent_course_id_field_is_rejected(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("course:add_comment"), {"comments": "x"})

        self.assertEqual(response.json(), {"status": "fail", "msg": "添加失败"})

    def test_unknown_course_id_answers_with_json(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("course:add_comment"),
            {"course_id": 999999, "comments": "x"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "fail", "msg": "课程不存在"})


class CourseAdminTests(TestCase):
    def setUp(self):
        self.client.force_login(make_superuser())
        self.course = make_course(name="普通课程")
        self.banner = make_course(
            name="轮播课程", org=self.course.course_org, is_banner=True
        )

    def test_admin_pages_render(self):
        urls = [
            reverse("admin:courses_course_changelist"),
            reverse("admin:courses_bannercourse_changelist"),
            reverse("admin:courses_lesson_changelist"),
            reverse("admin:courses_video_changelist"),
            reverse("admin:courses_courseresource_changelist"),
            reverse("admin:courses_course_add"),
            reverse("admin:courses_course_change", args=[self.course.id]),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_course_and_banner_lists_are_split(self):
        request = RequestFactory().get("/")
        course_admin = CourseAdmin(Course, admin_site=admin_site)
        banner_admin = BannerCourseAdmin(Course, admin_site=admin_site)

        self.assertEqual(
            [c.name for c in course_admin.get_queryset(request)], ["普通课程"]
        )
        self.assertEqual(
            [c.name for c in banner_admin.get_queryset(request)], ["轮播课程"]
        )

    def test_banner_admin_marks_course_as_banner_and_counts(self):
        request = RequestFactory().get("/")
        banner_admin = BannerCourseAdmin(Course, admin_site=admin_site)

        self.banner.is_banner = False
        banner_admin.save_model(request, self.banner, None, change=True)

        self.banner.refresh_from_db()
        self.assertTrue(self.banner.is_banner)
        self.assertEqual(self.banner.course_org.course_nums, 2)
