from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import (
    BooleanRadioFilter,
    ChoicesDropdownFilter,
    FieldTextFilter,
    RangeDateTimeFilter,
    RelatedDropdownFilter,
)

from admin import admin_site

from .models import CourseComments, UserAsk, UserCourse, UserFavorite, UserMessage


@admin.register(UserAsk, site=admin_site)
class UserAskAdmin(ModelAdmin):
    list_display = ["name", "mobile", "course_name", "add_time"]
    ordering = ["-add_time"]
    search_fields = ["name", "mobile", "course_name"]
    list_filter = [("course_name", FieldTextFilter), ("add_time", RangeDateTimeFilter)]


@admin.register(CourseComments, site=admin_site)
class CourseCommentsAdmin(ModelAdmin):
    list_display = ["user", "course", "comments", "add_time"]
    ordering = ["-add_time"]
    search_fields = ["user__username", "course__name", "comments"]
    list_select_related = ["user", "course"]
    list_filter = [("course", RelatedDropdownFilter), ("add_time", RangeDateTimeFilter)]


@admin.register(UserFavorite, site=admin_site)
class UserFavoriteAdmin(ModelAdmin):
    list_display = ["user", "fav_id", "fav_type", "add_time"]
    ordering = ["-add_time"]
    search_fields = ["user__username"]
    list_select_related = ["user"]
    list_filter = [
        ("fav_type", ChoicesDropdownFilter),
        ("add_time", RangeDateTimeFilter),
    ]


@admin.register(UserMessage, site=admin_site)
class UserMessageAdmin(ModelAdmin):
    list_display = ["user", "message", "has_read", "add_time"]
    ordering = ["-add_time"]
    search_fields = ["message"]
    list_filter = [
        ("has_read", BooleanRadioFilter),
        ("add_time", RangeDateTimeFilter),
    ]


@admin.register(UserCourse, site=admin_site)
class UserCourseAdmin(ModelAdmin):
    list_display = ["user", "course", "add_time"]
    ordering = ["-add_time"]
    search_fields = ["user__username", "course__name"]
    list_select_related = ["user", "course"]
    list_filter = [("course", RelatedDropdownFilter), ("add_time", RangeDateTimeFilter)]
