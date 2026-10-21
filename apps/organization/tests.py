from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from operation.models import UserAsk, UserFavorite
from organization.models import CourseOrg, Teacher
from utils.testing import (
    make_city,
    make_course,
    make_org,
    make_superuser,
    make_teacher,
    make_user,
)


def orgs_page(response):
    return response.context["all_orgs"]


class OrgListViewTests(TestCase):
    def setUp(self):
        self.guangzhou = make_city(name="广州")
        self.shenzhen = make_city(name="深圳")
        now = timezone.now()
        for index in range(6):
            make_org(
                name=f"培训机构 {index}",
                desc=f"<p>机构介绍 {index}</p>",
                city=self.guangzhou,
                category="pxjg",
                click_num=index,
                students=index,
                course_nums=6 - index,
                add_time=now - timezone.timedelta(days=index),
            )
        self.university = make_org(
            name="中山大学",
            desc="<p>高校介绍</p>",
            city=self.shenzhen,
            category="gx",
            click_num=3,
            students=100,
            course_nums=1,
            add_time=now,
        )

    def test_pagination_and_total_count(self):
        response = self.client.get(reverse("org:org_list"))

        self.assertEqual(orgs_page(response).paginator.num_pages, 2)
        self.assertEqual(len(orgs_page(response).object_list), 5)
        self.assertEqual(response.context["org_nums"], 7)

    def test_out_of_range_page_falls_back_to_last(self):
        response = self.client.get(reverse("org:org_list"), {"page": 40})

        self.assertEqual(orgs_page(response).number, 2)
        self.assertEqual(len(orgs_page(response).object_list), 2)

    def test_city_filter(self):
        filtered = self.client.get(reverse("org:org_list"), {"city": self.shenzhen.id})

        self.assertEqual([o.name for o in orgs_page(filtered)], ["中山大学"])
        self.assertEqual(filtered.context["city_id"], self.shenzhen.id)
        self.assertContains(filtered, '<span class="active2">深圳</span>', html=True)
        self.assertNotContains(filtered, '<span class="active2">广州</span>', html=True)

    def test_non_numeric_city_is_ignored(self):
        response = self.client.get(reverse("org:org_list"), {"city": "abc"})

        self.assertEqual(response.context["org_nums"], 7)

    def test_category_filter(self):
        response = self.client.get(reverse("org:org_list"), {"ct": "gx"})

        self.assertEqual([o.name for o in orgs_page(response)], ["中山大学"])

    def test_sorting(self):
        students = self.client.get(reverse("org:org_list"), {"sort": "students"})
        self.assertEqual(orgs_page(students)[0].name, "中山大学")

        courses = self.client.get(reverse("org:org_list"), {"sort": "courses"})
        self.assertEqual([o.course_nums for o in orgs_page(courses)], [6, 5, 4, 3, 2])

    def test_search_matches_name_and_desc(self):
        by_name = self.client.get(reverse("org:org_list"), {"keywords": "大学"})
        self.assertEqual([o.name for o in orgs_page(by_name)], ["中山大学"])

        by_desc = self.client.get(reverse("org:org_list"), {"keywords": "机构介绍 3"})
        self.assertEqual([o.name for o in orgs_page(by_desc)], ["培训机构 3"])

    def test_hot_orgs_ignore_filters(self):
        response = self.client.get(reverse("org:org_list"), {"keywords": "大学"})

        self.assertEqual([o.click_num for o in response.context["hot_orgs"]], [5, 4, 3])


class AddUserAskViewTests(TestCase):
    def test_valid_ask_is_saved(self):
        response = self.client.post(
            reverse("org:add_ask"),
            {
                "name": "小李",
                "mobile": "13800138000",
                "course_name": "Django 实战",
            },
        )

        self.assertEqual(response.json(), {"status": "success"})
        self.assertEqual(UserAsk.objects.count(), 1)

    def test_illegal_mobile_is_rejected(self):
        response = self.client.post(
            reverse("org:add_ask"),
            {
                "name": "小李",
                "mobile": "12345",
                "course_name": "Django 实战",
            },
        )

        self.assertEqual(response.json(), {"status": "fail", "msg": "手机号码非法"})
        self.assertEqual(UserAsk.objects.count(), 0)

    def test_missing_field_returns_first_error(self):
        response = self.client.post(
            reverse("org:add_ask"), {"mobile": "13800138000", "course_name": "课程"}
        )

        payload = response.json()
        self.assertEqual(payload["status"], "fail")
        self.assertTrue(payload["msg"])


class AddFavViewTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.org = make_org()
        self.teacher = make_teacher(self.org)
        self.course = make_course(org=self.org, teacher=self.teacher)

    def test_anonymous_user_is_asked_to_login(self):
        response = self.client.post(
            reverse("org:add_fav"), {"fav_id": self.course.id, "fav_type": 1}
        )

        self.assertEqual(response.json(), {"status": "fail", "msg": "用户未登录"})

    def test_favorite_course_then_cancel(self):
        self.client.force_login(self.user)

        first = self.client.post(
            reverse("org:add_fav"), {"fav_id": self.course.id, "fav_type": 1}
        )
        self.assertEqual(first.json(), {"status": "success", "msg": "已收藏"})
        self.course.refresh_from_db()
        self.assertEqual(self.course.fav_nums, 1)

        second = self.client.post(
            reverse("org:add_fav"), {"fav_id": self.course.id, "fav_type": 1}
        )
        self.assertEqual(second.json(), {"status": "success", "msg": "收藏"})
        self.course.refresh_from_db()
        self.assertEqual(self.course.fav_nums, 0)
        self.assertFalse(
            UserFavorite.objects.filter(user=self.user, fav_type=1).exists()
        )

    def test_favorite_org_and_teacher_use_their_own_counters(self):
        self.client.force_login(self.user)

        self.client.post(reverse("org:add_fav"), {"fav_id": self.org.id, "fav_type": 2})
        self.client.post(
            reverse("org:add_fav"), {"fav_id": self.teacher.id, "fav_type": 3}
        )

        self.org.refresh_from_db()
        self.teacher.refresh_from_db()
        self.assertEqual(self.org.fav_num, 1)
        self.assertEqual(self.teacher.fav_num, 1)

    def test_cancelling_a_favorite_never_goes_below_zero(self):
        self.client.force_login(self.user)
        UserFavorite.objects.create(user=self.user, fav_id=self.course.id, fav_type=1)

        self.client.post(
            reverse("org:add_fav"), {"fav_id": self.course.id, "fav_type": 1}
        )

        self.course.refresh_from_db()
        self.assertEqual(self.course.fav_nums, 0)

    def test_bad_requests_are_rejected(self):
        self.client.force_login(self.user)

        payloads = [
            {"fav_id": "", "fav_type": "1"},
            {"fav_id": "abc", "fav_type": "1"},
            {"fav_id": str(self.course.id), "fav_type": "9"},
            {"fav_id": "999999", "fav_type": "1"},
        ]
        for payload in payloads:
            with self.subTest(**payload):
                response = self.client.post(reverse("org:add_fav"), payload)
                self.assertEqual(response.json(), {"status": "fail", "msg": "收藏出错"})

        self.assertEqual(UserFavorite.objects.count(), 0)
        self.course.refresh_from_db()
        self.assertEqual(self.course.fav_nums, 0)


class OrgDetailTests(TestCase):
    def setUp(self):
        self.org = make_org(name="问渠机构", desc="<p>机构介绍</p>")
        self.teacher = make_teacher(self.org, name="张老师")
        now = timezone.now()
        for index in range(3):
            make_course(
                name=f"机构课程 {index}",
                org=self.org,
                teacher=self.teacher,
                add_time=now - timezone.timedelta(days=index),
            )

    def test_home_page_counts_click_and_limits_lists(self):
        extra_teacher = make_teacher(self.org, name="李老师")
        extra_course = make_course(
            name="第四条课程", org=self.org, teacher=extra_teacher
        )

        response = self.client.get(reverse("org:org_home", args=[self.org.id]))

        self.org.refresh_from_db()
        self.assertEqual(self.org.click_num, 1)
        # 首页预览取最新三条，顺序与“查看更多”列表首页一致
        self.assertEqual(
            [c.name for c in response.context["all_courses"]],
            [extra_course.name, "机构课程 0", "机构课程 1"],
        )
        self.assertEqual([t.name for t in response.context["all_teachers"]], ["李老师"])
        self.assertIn("<p>机构介绍</p>", response.content.decode("utf-8"))

    def test_course_page_paginates_three_per_page(self):
        make_course(
            name="第四条课程",
            org=self.org,
            teacher=self.teacher,
            add_time=timezone.now() + timezone.timedelta(days=1),
        )

        response = self.client.get(reverse("org:org_course", args=[self.org.id]))

        page = response.context["all_courses"]
        self.assertEqual(page.paginator.per_page, 3)
        self.assertEqual(page.paginator.num_pages, 2)
        self.assertEqual(
            [c.name for c in page.object_list], ["第四条课程", "机构课程 0", "机构课程 1"]
        )

        second = self.client.get(
            reverse("org:org_course", args=[self.org.id]), {"page": 2}
        )
        self.assertEqual(
            [c.name for c in second.context["all_courses"].object_list], ["机构课程 2"]
        )

    def test_teacher_page_lists_all_teachers(self):
        make_teacher(self.org, name="李老师")

        response = self.client.get(reverse("org:org_teacher", args=[self.org.id]))

        self.assertEqual(
            [t.name for t in response.context["all_teachers"]], ["张老师", "李老师"]
        )

    def test_desc_page_renders_rich_text(self):
        response = self.client.get(reverse("org:org_desc", args=[self.org.id]))

        self.assertIn("<p>机构介绍</p>", response.content.decode("utf-8"))
        self.assertNotIn("&lt;p&gt;", response.content.decode("utf-8"))

    def test_missing_org_returns_404(self):
        for url_name in ("org_home", "org_course", "org_desc", "org_teacher"):
            with self.subTest(url_name):
                response = self.client.get(
                    reverse(f"org:{url_name}", args=[999999])
                )
                self.assertEqual(response.status_code, 404)


class TeacherListTests(TestCase):
    def setUp(self):
        org = make_org()
        now = timezone.now()
        for index in range(6):
            make_teacher(
                org,
                name=f"讲师 {index}",
                work_company=f"公司 {index}",
                work_position=f"岗位 {index}",
                click_num=index,
                add_time=now - timezone.timedelta(days=index),
            )
        self.other_org = make_org(name="另一家机构")
        make_teacher(self.other_org, name="外包讲师", click_num=9)

    def test_pagination_uses_newest_first(self):
        response = self.client.get(reverse("org:teacher_list"))

        self.assertEqual(response.context["teachers_nums"], 7)
        self.assertEqual(
            [t.name for t in response.context["all_teachers"]],
            ["外包讲师"] + [f"讲师 {i}" for i in range(4)],
        )

    def test_search_matches_name_company_position(self):
        for keywords, expected in (
            ("讲师 1", "讲师 1"),
            ("公司 2", "讲师 2"),
            ("岗位 3", "讲师 3"),
        ):
            with self.subTest(keywords=keywords):
                response = self.client.get(
                    reverse("org:teacher_list"), {"keywords": keywords}
                )
                self.assertEqual(
                    [t.name for t in response.context["all_teachers"]], [expected]
                )

    def test_sort_by_hot(self):
        response = self.client.get(reverse("org:teacher_list"), {"sort": "hot"})

        self.assertEqual(
            [t.click_num for t in response.context["all_teachers"]], [9, 5, 4, 3, 2]
        )
        self.assertEqual(
            [t.click_num for t in response.context["sorted_teachers"]], [9, 5, 4]
        )


class TeacherDetailTests(TestCase):
    def setUp(self):
        self.org = make_org()
        self.teacher = make_teacher(self.org, name="张老师")
        self.course = make_course(name="张老师的课", org=self.org, teacher=self.teacher)
        make_course(
            name="别人的课", org=self.org, teacher=make_teacher(self.org, name="李老师")
        )

    def test_page_shows_only_own_courses_and_counts_click(self):
        response = self.client.get(
            reverse("org:teacher_detail", args=[self.teacher.id])
        )

        self.teacher.refresh_from_db()
        self.assertEqual(self.teacher.click_num, 1)
        self.assertEqual(
            [c.name for c in response.context["all_courses"]], ["张老师的课"]
        )

    def test_favorite_flags_for_teacher_and_org(self):
        user = make_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse("org:teacher_detail", args=[self.teacher.id])
        )
        self.assertFalse(response.context["has_teacher_faved"])
        self.assertFalse(response.context["has_org_faved"])

        self.client.post(
            reverse("org:add_fav"), {"fav_id": self.teacher.id, "fav_type": 3}
        )
        self.client.post(reverse("org:add_fav"), {"fav_id": self.org.id, "fav_type": 2})

        response = self.client.get(
            reverse("org:teacher_detail", args=[self.teacher.id])
        )
        self.assertTrue(response.context["has_teacher_faved"])
        self.assertTrue(response.context["has_org_faved"])

    def test_missing_teacher_returns_404(self):
        response = self.client.get(reverse("org:teacher_detail", args=[999999]))

        self.assertEqual(response.status_code, 404)


class OrganizationAdminTests(TestCase):
    def setUp(self):
        self.client.force_login(make_superuser())
        self.city = make_city(name="广州")
        self.org = CourseOrg.objects.create(
            name="问渠机构", desc="介绍", city=self.city, address="天河路"
        )
        self.teacher = Teacher.objects.create(org=self.org, name="张老师")

    def test_admin_pages_render(self):
        urls = [
            reverse("admin:organization_citydict_changelist"),
            reverse("admin:organization_courseorg_changelist"),
            reverse("admin:organization_courseorg_add"),
            reverse("admin:organization_courseorg_change", args=[self.org.id]),
            reverse("admin:organization_teacher_changelist"),
            reverse("admin:organization_teacher_change", args=[self.teacher.id]),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_city_autocomplete_field_works(self):
        make_city(name="深圳")

        response = self.client.get(
            reverse("admin:autocomplete"),
            {
                "app_label": "organization",
                "model_name": "courseorg",
                "field_name": "city",
                "term": "广州",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [(r["id"], r["text"]) for r in response.json()["results"]],
            [(str(self.city.id), "广州")],
        )

    def test_changelist_queries_do_not_grow_with_rows(self):
        def query_count(org_nums):
            CourseOrg.objects.all().delete()
            for index in range(org_nums):
                org = CourseOrg.objects.create(name=f"机构 {index}", city=self.city)
                for offset in range(3):
                    Teacher.objects.create(org=org, name=f"讲师 {index}-{offset}")

            with CaptureQueriesContext(connection) as queries:
                response = self.client.get(
                    reverse("admin:organization_courseorg_changelist")
                )
            self.assertEqual(response.status_code, 200)
            return len(queries)

        # 教师数、课程数是注解取回的，行数增加也不该多发查询
        self.assertEqual(query_count(2), query_count(6))
