"""测试对象工厂：机构、讲师、课程这类多表关联对象在多个 app 的用例里重复构造。"""

from courses.models import Course
from organization.models import CityDict, CourseOrg, Teacher
from users.models import UserProfile


def make_user(
    username="xiaoming", email="xiaoming@example.com", password="testpass123", **kwargs
):
    kwargs.setdefault("is_active", True)
    user = UserProfile.objects.create(username=username, email=email, **kwargs)
    user.set_password(password)
    user.save(update_fields=["password"])
    return user


def make_superuser(username="root", email="root@example.com", password="rootpass123"):
    return make_user(
        username=username,
        email=email,
        password=password,
        is_staff=True,
        is_superuser=True,
    )


def make_city(name="广州", desc="华南"):
    return CityDict.objects.create(name=name, desc=desc)


def make_org(name="问渠机构", **kwargs):
    kwargs.setdefault("city", make_city())
    kwargs.setdefault("desc", "<p>机构介绍</p>")
    return CourseOrg.objects.create(name=name, address="天河路 1 号", **kwargs)


def make_teacher(org=None, name="张老师", **kwargs):
    return Teacher.objects.create(org=org or make_org(), name=name, **kwargs)


def make_course(name="Django 入门", org=None, teacher=None, **kwargs):
    org = org or make_org()
    kwargs.setdefault("desc", "从零开始的 Django 课程")
    kwargs.setdefault("detail", "<p>课程详情</p>")
    kwargs.setdefault("degree", "cj")
    return Course.objects.create(
        name=name, course_org=org, teacher=teacher or make_teacher(org), **kwargs
    )
