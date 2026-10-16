from courses.models import Course
from django.db import models
from django.utils import timezone
from users.models import UserProfile


class UserAsk(models.Model):
    name = models.CharField(max_length=20, verbose_name="姓名")
    mobile = models.CharField(max_length=11, verbose_name="手机")
    course_name = models.CharField(max_length=50, verbose_name="课程名")
    add_time = models.DateTimeField(default=timezone.now, verbose_name="添加时间")

    class Meta:
        verbose_name = "用户咨询"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.name} 咨询 {self.course_name}"


class CourseComments(models.Model):
    user = models.ForeignKey(UserProfile, verbose_name="用户", on_delete=models.CASCADE)
    course = models.ForeignKey(Course, verbose_name="课程", on_delete=models.CASCADE)
    comments = models.CharField(max_length=200, verbose_name="评论")
    add_time = models.DateTimeField(default=timezone.now, verbose_name="添加时间")

    class Meta:
        verbose_name = "课程评论"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.user} 评论 {self.course}"


class UserFavorite(models.Model):
    # fav_type 的取值在课程/机构/讲师三个 app 的视图里都会用到，集中定义一次
    COURSE = 1
    ORG = 2
    TEACHER = 3

    user = models.ForeignKey(UserProfile, verbose_name="用户", on_delete=models.CASCADE)
    fav_id = models.IntegerField(default=0, verbose_name="数据id")
    fav_type = models.IntegerField(
        choices=((COURSE, "课程"), (ORG, "课程机构"), (TEACHER, "讲师")),
        default=COURSE,
        verbose_name="收藏类型",
    )
    add_time = models.DateTimeField(default=timezone.now, verbose_name="添加时间")

    class Meta:
        verbose_name = "用户收藏"
        verbose_name_plural = verbose_name
        constraints = [
            models.UniqueConstraint(
                fields=["user", "fav_id", "fav_type"], name="uniq_user_favorite"
            ),
        ]

    def __str__(self):
        return f"{self.user} 收藏 {self.get_fav_type_display()}"


class UserMessage(models.Model):
    user = models.IntegerField(default=0, verbose_name="接受用户")
    message = models.CharField(max_length=500, verbose_name="消息内容")
    has_read = models.BooleanField(default=False, verbose_name="是否已读")
    add_time = models.DateTimeField(default=timezone.now, verbose_name="添加时间")

    class Meta:
        verbose_name = "用户消息"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.user}: {self.message[:20]}"


class UserCourse(models.Model):
    user = models.ForeignKey(UserProfile, verbose_name="用户", on_delete=models.CASCADE)
    course = models.ForeignKey(Course, verbose_name="课程", on_delete=models.CASCADE)
    add_time = models.DateTimeField(default=timezone.now, verbose_name="添加时间")

    class Meta:
        verbose_name = "用户课程"
        verbose_name_plural = verbose_name
        constraints = [
            models.UniqueConstraint(
                fields=["user", "course"], name="uniq_user_course"
            ),
        ]

    def __str__(self):
        return f"{self.user} 学习 {self.course}"
