from django.contrib import admin
from django.db.models import Count
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import ChoicesDropdownFilter, RangeDateTimeFilter

from admin import admin_site

from .models import BannerCourse, Course, CourseResource, Lesson, Video


class LessonInline(TabularInline):
    model = Lesson
    extra = 0


class CourseResourceInline(TabularInline):
    model = CourseResource
    extra = 0


class CourseBaseAdmin(ModelAdmin):
    list_display = [
        "name",
        "desc",
        "degree",
        "learn_times",
        "students",
        "lesson_nums",
        "go_to",
    ]
    search_fields = ["name", "desc", "detail", "learn_times", "students"]
    list_filter = [
        ("degree", ChoicesDropdownFilter),
        ("category", ChoicesDropdownFilter),
        ("add_time", RangeDateTimeFilter),
    ]
    ordering = ["-click_nums"]
    readonly_fields = ["click_nums"]
    exclude = ["fav_nums"]
    inlines = [LessonInline, CourseResourceInline]
    list_editable = ["degree", "desc"]

    def get_queryset(self, request):
        # 章节数一次注解取回，避免每行发一条 COUNT
        return super().get_queryset(request).annotate(lesson_nums=Count("lesson"))

    @admin.display(description="章节数", ordering="lesson_nums")
    def lesson_nums(self, obj):
        return obj.lesson_nums


@admin.register(Course, site=admin_site)
class CourseAdmin(CourseBaseAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_banner=False)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # 保存课程后重新统计所属机构的课程数
        obj.refresh_course_nums()


@admin.register(BannerCourse, site=admin_site)
class BannerCourseAdmin(CourseBaseAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_banner=True)

    def save_model(self, request, obj, form, change):
        obj.is_banner = True
        super().save_model(request, obj, form, change)
        obj.refresh_course_nums()


@admin.register(Lesson, site=admin_site)
class LessonAdmin(ModelAdmin):
    list_display = ["course", "name", "add_time"]
    search_fields = ["course__name", "name"]
    list_select_related = ["course"]
    list_filter = [("course", ChoicesDropdownFilter), ("add_time", RangeDateTimeFilter)]


@admin.register(Video, site=admin_site)
class VideoAdmin(ModelAdmin):
    list_display = ["lesson", "name", "learn_times", "add_time"]
    search_fields = ["lesson__name", "name"]
    list_select_related = ["lesson"]
    list_filter = [("lesson", ChoicesDropdownFilter), ("add_time", RangeDateTimeFilter)]


@admin.register(CourseResource, site=admin_site)
class CourseResourceAdmin(ModelAdmin):
    list_display = ["course", "name", "download", "add_time"]
    search_fields = ["course__name", "name"]
    list_select_related = ["course"]
    list_filter = [("course", ChoicesDropdownFilter), ("add_time", RangeDateTimeFilter)]
