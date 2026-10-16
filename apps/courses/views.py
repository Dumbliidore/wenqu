from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.generic.base import View
from operation.models import CourseComments, UserCourse, UserFavorite
from utils.favorites import is_faved
from utils.pagination import paginate

from .models import Course, CourseResource

PAGE_SIZE = 6


def get_popular_courses(course, limit=5):
    """推荐课程：学过本课的用户还学过哪些课。"""
    user_ids = UserCourse.objects.filter(course=course).values_list(
        "user_id", flat=True
    )
    course_ids = (
        UserCourse.objects.filter(user_id__in=user_ids)
        .exclude(course=course)
        .values_list("course_id", flat=True)
    )
    return (
        Course.objects.filter(id__in=course_ids)
        .select_related("course_org", "teacher")
        .order_by("-click_nums")[:limit]
    )


class CourseListView(View):
    """
    课程列表功能
    """

    def get(self, request):
        all_courses = Course.objects.select_related("course_org", "teacher").order_by(
            "-add_time"
        )
        hot_courses = Course.objects.select_related("course_org", "teacher").order_by(
            "-click_nums"
        )[:3]

        search_keywords = request.GET.get("keywords", "")
        if search_keywords:
            all_courses = all_courses.filter(
                Q(name__icontains=search_keywords)
                | Q(desc__icontains=search_keywords)
                | Q(detail__icontains=search_keywords)
            )

        sort = request.GET.get("sort", "")
        if sort == "students":
            all_courses = all_courses.order_by("-students")
        elif sort == "hot":
            all_courses = all_courses.order_by("-click_nums")

        return render(
            request,
            "course-list.html",
            {
                "all_courses": paginate(request, all_courses, PAGE_SIZE),
                "sort": sort,
                "hot_courses": hot_courses,
            },
        )


class CourseDetailView(View):
    """
    课程详情页
    """

    def get(self, request, course_id):
        course = get_object_or_404(
            Course.objects.select_related("course_org", "teacher"), id=course_id
        )

        # 增加课程点击数，用 F 表达式避免并发覆盖
        Course.objects.filter(id=course.id).update(click_nums=F("click_nums") + 1)
        course.click_nums += 1

        relate_courses = []
        if course.tag:
            relate_courses = (
                Course.objects.select_related("course_org", "teacher")
                .filter(tag=course.tag)
                .exclude(id=course.id)
                .order_by("-click_nums")[:1]
            )

        has_fav_course = is_faved(request, course.id, UserFavorite.COURSE)
        has_fav_org = is_faved(request, course.course_org_id, UserFavorite.ORG)

        return render(
            request,
            "course-detail.html",
            {
                "course": course,
                "relate_courses": relate_courses,
                "has_fav_course": has_fav_course,
                "has_fav_org": has_fav_org,
            },
        )


class CourseInfoView(LoginRequiredMixin, View):
    """
    课程章节信息
    """

    def get(self, request, course_id):
        course = get_object_or_404(
            Course.objects.select_related("course_org", "teacher"), id=course_id
        )
        # 学习人数只在第一次进入时累加，重复访问不再写库
        _, created = UserCourse.objects.get_or_create(user=request.user, course=course)
        if created:
            Course.objects.filter(id=course.id).update(students=F("students") + 1)
            course.students += 1

        return render(
            request,
            "course-video.html",
            {
                "course": course,
                "course_resources": CourseResource.objects.filter(course=course),
                "relate_courses": get_popular_courses(course),
            },
        )


class CommentView(LoginRequiredMixin, View):
    """
    课程评论页显示
    """

    def get(self, request, course_id):
        course = get_object_or_404(
            Course.objects.select_related("course_org", "teacher"), id=course_id
        )
        return render(
            request,
            "course-comment.html",
            {
                "course": course,
                "course_resources": CourseResource.objects.filter(course=course),
                "all_comments": CourseComments.objects.filter(course=course)
                .select_related("user")
                .order_by("-add_time"),
                "relate_courses": get_popular_courses(course),
            },
        )


class AddCommentView(View):
    """
    用户添加课程评论
    """

    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({"status": "fail", "msg": "用户未登录"})

        # 默认值必须是字符串，否则缺字段时 .isdigit() 直接报 500
        course_id = request.POST.get("course_id", "")
        comments = request.POST.get("comments", "")
        if not course_id.isdigit() or int(course_id) <= 0 or not comments:
            return JsonResponse({"status": "fail", "msg": "添加失败"})

        course = Course.objects.filter(id=int(course_id)).first()
        if course is None:
            # AJAX 接口统一回 JSON，不能返回 404 页面
            return JsonResponse({"status": "fail", "msg": "课程不存在"})

        CourseComments.objects.create(
            course=course, comments=comments, user=request.user
        )
        return JsonResponse({"status": "success", "msg": "添加成功"})
