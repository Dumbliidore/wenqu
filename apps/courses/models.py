from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django_ckeditor_5.fields import CKEditor5Field
from organization.models import CourseOrg, Teacher


class Course(models.Model):
    course_org = models.ForeignKey(
        CourseOrg, verbose_name="课程机构", on_delete=models.CASCADE
    )
    teacher = models.ForeignKey(Teacher, verbose_name="讲师", on_delete=models.CASCADE)
    name = models.CharField(max_length=50, verbose_name="课程名")
    desc = models.CharField(max_length=300, verbose_name="课程描述")
    detail = CKEditor5Field(verbose_name="课程详情", config_name="extends", blank=True)
    is_banner = models.BooleanField(default=False, verbose_name="是否轮播")
    category = models.CharField(
        default="后端开发", max_length=20, verbose_name="课程类别"
    )
    degree = models.CharField(
        verbose_name="难度",
        choices=(("cj", "初级"), ("zj", "中级"), ("gj", "高级")),
        max_length=2,
    )
    learn_times = models.IntegerField(default=0, verbose_name="学习时长(分钟数)")
    students = models.IntegerField(default=0, verbose_name="学习人数")
    fav_nums = models.IntegerField(default=0, verbose_name="收藏人数")
    tag = models.CharField(default="", verbose_name="课程标签", max_length=10)
    image = models.ImageField(
        upload_to="courses/%Y/%m", verbose_name="封面图", max_length=100
    )
    click_nums = models.IntegerField(default=0, verbose_name="点击数")
    add_time = models.DateTimeField(default=timezone.now, verbose_name="添加时间")
    youneed_know = models.CharField(default="", max_length=50, verbose_name="课程须知")
    teacher_tell = models.CharField(
        default="", max_length=50, verbose_name="老师告诉你"
    )

    class Meta:
        verbose_name = "课程"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

    def get_zj_nums(self):
        return self.lesson_set.count()

    get_zj_nums.short_description = "章节数"

    def go_to(self):
        link = reverse("course:course_detail", args=[self.id])
        return mark_safe(f'<a href="{link}">课程详情</a>')

    go_to.short_description = "跳转"

    def get_learn_users(self):
        return self.usercourse_set.all()[:5]

    def get_course_lesson(self):
        return self.lesson_set.all()

    def refresh_course_nums(self):
        # 机构上的 course_nums 是冗余统计，保存课程后要重新对齐
        with transaction.atomic():
            org = self.course_org
            org.course_nums = Course.objects.filter(course_org=org).count()
            org.save(update_fields=["course_nums"])


class BannerCourse(Course):
    class Meta:
        verbose_name = "轮播课程"
        verbose_name_plural = verbose_name
        proxy = True


class Lesson(models.Model):
    course = models.ForeignKey(Course, verbose_name="课程", on_delete=models.CASCADE)
    name = models.CharField(max_length=100, verbose_name="章节名")
    add_time = models.DateTimeField(default=timezone.now, verbose_name="添加时间")

    class Meta:
        verbose_name = "章节"
        verbose_name_plural = verbose_name
        ordering = ["id"]

    def __str__(self):
        return self.name

    def get_lesson_video(self):
        return self.video_set.all()


class Video(models.Model):
    lesson = models.ForeignKey(Lesson, verbose_name="章节", on_delete=models.CASCADE)
    url = models.CharField(max_length=200, verbose_name="访问地址", default="")
    name = models.CharField(max_length=100, verbose_name="视频名称")
    learn_times = models.IntegerField(default=0, verbose_name="学习时长(分钟数)")
    add_time = models.DateTimeField(default=timezone.now, verbose_name="添加时间")

    class Meta:
        verbose_name = "视频"
        verbose_name_plural = verbose_name
        ordering = ["id"]

    def __str__(self):
        return self.name


class CourseResource(models.Model):
    course = models.ForeignKey(Course, verbose_name="课程", on_delete=models.CASCADE)
    name = models.CharField(max_length=100, verbose_name="名称")
    download = models.FileField(
        upload_to="course/resource/%Y%m", verbose_name="资源文件", max_length=100
    )
    add_time = models.DateTimeField(default=timezone.now, verbose_name="添加时间")

    class Meta:
        verbose_name = "课程资源"
        verbose_name_plural = verbose_name
        ordering = ["id"]

    def __str__(self):
        return self.name
