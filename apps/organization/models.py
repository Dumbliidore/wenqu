from django.db import models
from django.utils import timezone
from django_ckeditor_5.fields import CKEditor5Field


class CityDict(models.Model):
    name = models.CharField(max_length=20, verbose_name="城市")
    desc = models.CharField(max_length=200, verbose_name="描述")
    add_time = models.DateTimeField(default=timezone.now, verbose_name="添加时间")

    class Meta:
        verbose_name = "城市"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class CourseOrg(models.Model):
    name = models.CharField(max_length=50, verbose_name="机构名称")
    desc = CKEditor5Field(verbose_name="机构描述", config_name="extends", blank=True)
    tag = models.CharField(default="全国知名", max_length=10, verbose_name="机构标签")
    category = models.CharField(verbose_name="机构类别", default="pxjg", choices=(("pxjg", "培训机构"), ("gr", "个人"), ("gx", "高校")), max_length=20)
    click_num = models.IntegerField(default=0, verbose_name="点击数")
    fav_num = models.IntegerField(default=0, verbose_name="收藏数")
    image = models.ImageField(upload_to="org/%Y/%m", verbose_name="logo", max_length=100)
    address = models.CharField(max_length=150, verbose_name="机构地址")
    city = models.ForeignKey(CityDict, verbose_name="所在城市", on_delete=models.PROTECT)
    students = models.IntegerField(default=0, verbose_name="学习人数")
    course_nums = models.IntegerField(default=0, verbose_name="课程数")
    add_time = models.DateTimeField(default=timezone.now, verbose_name="添加时间")

    class Meta:
        verbose_name = "课程机构"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

    def get_teacher_nums(self):
        return self.teacher_set.count()

    get_teacher_nums.short_description = "教师数"


class Teacher(models.Model):
    org = models.ForeignKey(CourseOrg, verbose_name="所属机构", on_delete=models.CASCADE)
    name = models.CharField(max_length=50, verbose_name="教师名")
    age = models.IntegerField(default=18, verbose_name="年龄")
    image = models.ImageField(default="", upload_to="teacher/%Y/%m", verbose_name="头像", max_length=100)
    work_year = models.IntegerField(default=0, verbose_name="工作年限")
    work_company = models.CharField(max_length=50, verbose_name="就职公司", default="")
    work_position = models.CharField(max_length=50, verbose_name="公司职位", default="")
    points = models.CharField(max_length=50, verbose_name="教学特点", default="")
    click_num = models.IntegerField(default=0, verbose_name="点击数")
    fav_num = models.IntegerField(default=0, verbose_name="收藏数")
    add_time = models.DateTimeField(default=timezone.now, verbose_name="添加时间")

    class Meta:
        verbose_name = "教师"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

    def get_course_nums(self):
        return self.course_set.count()

    get_course_nums.short_description = "课程数"
