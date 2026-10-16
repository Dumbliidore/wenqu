from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import (
    ChoicesDropdownFilter,
    RangeDateTimeFilter,
    RangeNumericFilter,
    RelatedDropdownFilter,
)
    
from admin import admin_site

from .models import CityDict, CourseOrg, Teacher


@admin.register(CityDict, site=admin_site)
class CityDictAdmin(ModelAdmin):
    list_display = ["name", "desc", "add_time"]
    search_fields = ["name", "desc"]
    ordering = ["name"]
    list_filter = [("add_time", RangeDateTimeFilter)]


@admin.register(CourseOrg, site=admin_site)
class CourseOrgAdmin(ModelAdmin):
    list_display = [
        "name",
        "category",
        "click_num",
        "fav_num",
        "students",
        "course_nums",
        "get_teacher_nums",
    ]
    search_fields = ["name", "desc"]
    list_filter = [
        ("category", ChoicesDropdownFilter),
        ("city", RelatedDropdownFilter),
        ("add_time", RangeDateTimeFilter),
    ]
    ordering = ["-click_num"]
    readonly_fields = ["click_num", "fav_num"]
    # 所在城市改为搜索选择，取代 xadmin 的 relfield_style = 'fk-ajax'
    autocomplete_fields = ["city"]


@admin.register(Teacher, site=admin_site)
class TeacherAdmin(ModelAdmin):
    list_display = [
        "org",
        "name",
        "work_year",
        "work_company",
        "click_num",
        "get_course_nums",
    ]
    search_fields = ["name", "work_company", "work_position"]
    list_filter = [
        ("org", RelatedDropdownFilter),
        ("work_year", RangeNumericFilter),
        ("add_time", RangeDateTimeFilter),
    ]
    ordering = ["-click_num"]
    readonly_fields = ["click_num", "fav_num"]
