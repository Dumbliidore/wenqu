from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as DjangoGroupAdmin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import (
    BooleanRadioFilter,
    ChoicesDropdownFilter,
    RangeDateTimeFilter,
)

from admin import admin_site

from .models import Banner, EmailVerifyRecord, UserProfile


@admin.register(UserProfile, site=admin_site)
class UserProfileAdmin(ModelAdmin, DjangoUserAdmin):
    list_display = [
        "username",
        "nick_name",
        "email",
        "mobile",
        "gender",
        "is_active",
        "date_joined",
    ]
    search_fields = ["username", "nick_name", "email", "mobile"]
    list_filter = [
        ("gender", ChoicesDropdownFilter),
        ("is_active", BooleanRadioFilter),
        ("date_joined", RangeDateTimeFilter),
    ]
    ordering = ["-date_joined"]
    fieldsets = DjangoUserAdmin.fieldsets + (
        (
            "额外信息",
            {"fields": ("nick_name", "birday", "gender", "address", "mobile", "image")},
        ),
    )
    readonly_fields = ["last_login", "date_joined"]


@admin.register(Group, site=admin_site)
class GroupAdmin(ModelAdmin, DjangoGroupAdmin):
    pass


@admin.register(EmailVerifyRecord, site=admin_site)
class EmailVerifyRecordAdmin(ModelAdmin):
    list_display = ["code", "email", "send_type", "send_time"]
    search_fields = ["code", "email", "send_type"]
    list_filter = [
        ("send_type", ChoicesDropdownFilter),
        ("send_time", RangeDateTimeFilter),
    ]


@admin.register(Banner, site=admin_site)
class BannerAdmin(ModelAdmin):
    list_display = ["title", "image", "url", "index", "add_time"]
    search_fields = ["title", "url", "index"]
    list_filter = ["index", ("add_time", RangeDateTimeFilter)]
