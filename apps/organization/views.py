from courses.models import Course
from django.db import transaction
from django.db.models import Count, F, Q
from django.db.models.functions import Greatest
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.generic.base import View
from operation.models import UserFavorite
from utils.favorites import is_faved
from utils.pagination import paginate

from .forms import UserAskForm
from .models import CityDict, CourseOrg, Teacher

# 演示库有 8 机构 / 12 讲师，每页 5 条就能出分页条。
# 机构课程页只放 1 条：单机构最多 4 门课，放 1 条才看得到分页条。
ORG_PAGE_SIZE = 5
ORG_COURSE_PAGE_SIZE = 1
TEACHER_PAGE_SIZE = 5
TOP_TEACHER_NUMS = 3
ORG_TOP_COURSE_NUMS = 2


def attach_top_courses(orgs):
    """给列表页每个机构挂上热门课程，一次查询按机构分组，避免逐个机构查库。"""
    courses_by_org = {}
    org_ids = [org.id for org in orgs]
    if not org_ids:
        return
    rows = (
        Course.objects.filter(course_org_id__in=org_ids)
        .order_by("-students")
        .values("id", "name", "course_org_id")
    )
    for row in rows:
        courses_by_org.setdefault(row["course_org_id"], []).append(row)
    for org in orgs:
        org.top_courses = courses_by_org.get(org.id, [])[:ORG_TOP_COURSE_NUMS]


class OrgView(View):
    """
    课程机构列表功能
    """

    def get(self, request):
        all_orgs = CourseOrg.objects.select_related("city").order_by("-add_time")
        hot_orgs = all_orgs.order_by("-click_num")[:3]
        all_citys = CityDict.objects.all()

        search_keywords = request.GET.get("keywords", "")
        if search_keywords:
            all_orgs = all_orgs.filter(
                Q(name__icontains=search_keywords) | Q(desc__icontains=search_keywords)
            )

        # 机构高亮需要与 city.id 比较，转成 int 再放进模板
        raw_city_id = request.GET.get("city", "")
        city_id = int(raw_city_id) if raw_city_id.isdigit() else ""
        if city_id:
            all_orgs = all_orgs.filter(city_id=city_id)

        category = request.GET.get("ct", "")
        if category:
            all_orgs = all_orgs.filter(category=category)

        sort = request.GET.get("sort", "")
        if sort == "students":
            all_orgs = all_orgs.order_by("-students")
        elif sort == "courses":
            all_orgs = all_orgs.order_by("-course_nums")

        orgs_page = paginate(request, all_orgs, ORG_PAGE_SIZE)
        attach_top_courses(orgs_page.object_list)

        return render(
            request,
            "org-list.html",
            {
                "all_orgs": orgs_page,
                "all_citys": all_citys,
                # 分页器内部已经数过一遍，直接取它的 count 省一次 COUNT 查询
                "org_nums": orgs_page.paginator.count,
                "city_id": city_id,
                "category": category,
                "hot_orgs": hot_orgs,
                "sort": sort,
            },
        )


class AddUserAskView(View):
    """
    用户添加咨询
    """

    def post(self, request):
        userask_form = UserAskForm(request.POST)
        if userask_form.is_valid():
            userask_form.save()
            return JsonResponse({"status": "success"})

        errors = userask_form.errors.get_json_data()
        msg = "提交失败"
        for field_errors in errors.values():
            if field_errors:
                msg = field_errors[0]["message"]
                break

        return JsonResponse({"status": "fail", "msg": msg})


class OrgHomeView(View):
    """
    机构首页
    """

    def get(self, request, org_id):
        course_org = get_object_or_404(CourseOrg, id=org_id)
        CourseOrg.objects.filter(id=course_org.id).update(click_num=F("click_num") + 1)
        course_org.click_num += 1

        return render(
            request,
            "org-detail-homepage.html",
            {
                # 切片前必须写死排序，否则换数据库后首页卡片顺序会变
                "all_courses": course_org.course_set.select_related("teacher").order_by(
                    "-add_time"
                )[:3],
                "all_teachers": course_org.teacher_set.select_related("org").order_by(
                    "-add_time"
                )[:1],
                "course_org": course_org,
                "current_page": "home",
                "has_fav": is_faved(request, course_org.id, UserFavorite.ORG),
            },
        )


class OrgCourseView(View):
    """
    机构课程列表首页
    """

    def get(self, request, org_id):
        course_org = get_object_or_404(CourseOrg, id=org_id)
        org_courses = course_org.course_set.select_related(
            "course_org", "teacher"
        ).order_by("-add_time")

        return render(
            request,
            "org-detail-course.html",
            {
                "all_courses": paginate(request, org_courses, ORG_COURSE_PAGE_SIZE),
                "course_org": course_org,
                "current_page": "course",
                "has_fav": is_faved(request, course_org.id, UserFavorite.ORG),
            },
        )


class OrgDescView(View):
    """
    机构介绍页
    """

    def get(self, request, org_id):
        course_org = get_object_or_404(CourseOrg, id=org_id)

        return render(
            request,
            "org-detail-desc.html",
            {
                "course_org": course_org,
                "current_page": "desc",
                "has_fav": is_faved(request, course_org.id, UserFavorite.ORG),
            },
        )


class OrgTeacherView(View):
    """
    机构讲师页
    """

    def get(self, request, org_id):
        course_org = get_object_or_404(CourseOrg, id=org_id)
        # 模板要展示每位讲师的课程数，用注解一次算完，避免逐个讲师 count
        teachers = course_org.teacher_set.select_related("org").annotate(
            course_count=Count("course")
        )

        return render(
            request,
            "org-detail-teachers.html",
            {
                "all_teachers": teachers,
                "course_org": course_org,
                "current_page": "teacher",
                "has_fav": is_faved(request, course_org.id, UserFavorite.ORG),
            },
        )


class AddFavView(View):
    """
    用户收藏与取消收藏
    """

    TARGETS = {
        UserFavorite.COURSE: (Course, "fav_nums"),
        UserFavorite.ORG: (CourseOrg, "fav_num"),
        UserFavorite.TEACHER: (Teacher, "fav_num"),
    }

    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({"status": "fail", "msg": "用户未登录"})

        fav_id = request.POST.get("fav_id", "0")
        fav_type = request.POST.get("fav_type", "0")
        if not fav_id.isdigit() or not fav_type.isdigit():
            return JsonResponse({"status": "fail", "msg": "收藏出错"})

        fav_id, fav_type = int(fav_id), int(fav_type)
        if fav_id <= 0 or fav_type not in self.TARGETS:
            return JsonResponse({"status": "fail", "msg": "收藏出错"})

        target, counter = self.TARGETS[fav_type]
        instance = target.objects.filter(id=fav_id).first()
        if instance is None:
            return JsonResponse({"status": "fail", "msg": "收藏出错"})

        favorites = UserFavorite.objects.filter(
            user=request.user, fav_id=fav_id, fav_type=fav_type
        )
        # 收藏记录和计数字段一起改，中途失败才不会让数字和实际收藏脱钩
        with transaction.atomic():
            if favorites.exists():
                # 记录已存在表示取消收藏
                favorites.delete()
                target.objects.filter(id=fav_id).update(
                    **{counter: Greatest(F(counter) - 1, 0)}
                )
                msg = "收藏"
            else:
                _, created = UserFavorite.objects.get_or_create(
                    user=request.user, fav_id=fav_id, fav_type=fav_type
                )
                if created:
                    target.objects.filter(id=fav_id).update(
                        **{counter: F(counter) + 1}
                    )
                msg = "已收藏"

        return JsonResponse({"status": "success", "msg": msg})


class TeacherListView(View):
    """
    课程讲师列表页
    """

    def get(self, request):
        all_teachers = Teacher.objects.select_related("org").order_by("-add_time")

        search_keywords = request.GET.get("keywords", "")
        if search_keywords:
            all_teachers = all_teachers.filter(
                Q(name__icontains=search_keywords)
                | Q(work_company__icontains=search_keywords)
                | Q(work_position__icontains=search_keywords)
            )

        sort = request.GET.get("sort", "")
        if sort == "hot":
            all_teachers = all_teachers.order_by("-click_num")

        teachers_page = paginate(request, all_teachers, TEACHER_PAGE_SIZE)

        return render(
            request,
            "teachers-list.html",
            {
                "all_teachers": teachers_page,
                "sort": sort,
                "sorted_teachers": Teacher.objects.select_related("org").order_by(
                    "-click_num"
                )[:TOP_TEACHER_NUMS],
                # 分页器已经数过一遍，这里的 count 直接复用它
                "teachers_nums": teachers_page.paginator.count,
            },
        )


class TeacherDetailView(View):
    """
    讲师详情页
    """

    def get(self, request, teacher_id):
        teacher = get_object_or_404(
            Teacher.objects.select_related("org"), id=teacher_id
        )
        Teacher.objects.filter(id=teacher.id).update(click_num=F("click_num") + 1)
        teacher.click_num += 1

        has_teacher_faved = is_faved(request, teacher.id, UserFavorite.TEACHER)
        has_org_faved = is_faved(request, teacher.org_id, UserFavorite.ORG)

        return render(
            request,
            "teacher-detail.html",
            {
                "teacher": teacher,
                "all_courses": Course.objects.filter(teacher=teacher)
                .select_related("course_org", "teacher")
                .order_by("-add_time"),
                "sorted_teachers": Teacher.objects.select_related("org").order_by(
                    "-click_num"
                )[:TOP_TEACHER_NUMS],
                "has_teacher_faved": has_teacher_faved,
                "has_org_faved": has_org_faved,
            },
        )
