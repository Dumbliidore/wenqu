"""往开发库灌一批演示数据：机构、讲师、课程、用户、收藏、评论、消息等。

用法：DJANGO_SETTINGS_MODULE=settings.dev uv run python seed_demo.py
已有数据时直接退出，不会覆盖。
"""

import random
from datetime import timedelta

import django

django.setup()

from courses.models import Course, CourseResource, Lesson, Video
from django.utils import timezone
from operation.models import (
    CourseComments,
    UserAsk,
    UserCourse,
    UserFavorite,
    UserMessage,
)
from organization.models import CityDict, CourseOrg, Teacher
from users.models import Banner, EmailVerifyRecord, UserProfile

random.seed(20261013)

if CourseOrg.objects.exists() or UserProfile.objects.exists():
    raise SystemExit("库里已经有数据，先确认要清理还是补充")

now = timezone.now()

ORG_IMAGES = [
    "org/2018/04/imooc.png",
    "org/2018/04/bjdx.jpg",
    "org/2018/04/qhdx-logo.png",
    "org/2018/06/aobama_20161113225004_372.png",
]
COURSE_IMAGES = [
    "courses/2018/04/mysql.jpg",
    "courses/2018/04/540e57300001d6d906000338-240-135.jpg",
    "courses/2018/04/57035ff200014b8a06000338-240-135.jpg",
    "courses/2018/06/aobama_20161113225004_372.png",
]
TEACHER_IMAGES = [
    "teacher/2018/04/default_middile_1.png",
    "teacher/2018/04/default_middile_13_20161113185849_453.png",
    "teacher/2018/04/default_middile_14_20161113173158_261.png",
    "teacher/2018/04/default_middile_1_20161113172604_856.png",
]

# ---------------------------------------------------------------- 用户
USERS = [
    (
        "admin",
        "admin@example.com",
        "站点管理员",
        "admin123456",
        {
            "is_staff": True,
            "is_superuser": True,
            "gender": "male",
            "address": "广州市天河区",
            "mobile": "13800000001",
            "image": "image/2018/05/default_middile_1_20161113172604_856.png",
        },
    ),
    (
        "student",
        "student@example.com",
        "小李",
        "student123456",
        {
            "gender": "male",
            "address": "深圳市南山区",
            "mobile": "13800000002",
            "image": "image/2018/05/default_middile_14_20161113173158_261.png",
        },
    ),
    (
        "teacher01",
        "teacher01@example.com",
        "沈老师",
        "teacher123456",
        {"gender": "female", "address": "北京市海淀区"},
    ),
]
accounts = {}
for username, email, nickname, password, extra in USERS:
    user = UserProfile(username=username, email=email, nick_name=nickname, **extra)
    user.set_password(password)
    user.save()
    accounts[username] = user

pending = UserProfile(
    username="newbie",
    email="newbie@example.com",
    nick_name="待激活用户",
    is_active=False,
)
pending.set_password("newbie123456")
pending.save()
EmailVerifyRecord.objects.create(
    code="DEMO-ACTIVATE-CODE", email=pending.email, send_type="register"
)

student = accounts["student"]

# ---------------------------------------------------------------- 城市 / 机构 / 讲师 / 课程
cities = [
    CityDict.objects.create(name=name, desc=desc)
    for name, desc in [
        ("北京", "高校与培训机构集中"),
        ("上海", "前端与数据分析岗位多"),
        ("广州", "移动开发与后端岗位多"),
    ]
]

ORG_PLAN = [
    (
        "慕课网",
        "pxjg",
        2,
        "全国知名",
        "专注 IT 技能培训的在线教育平台，课程覆盖前后端、大数据与人工智能。",
    ),
    (
        "鱼C科技",
        "pxjg",
        0,
        "明星机构",
        "以零基础入门见长，主打 Python 与 C 语言系列课程。",
    ),
    (
        "老男孩教育",
        "pxjg",
        2,
        "就业推荐",
        "Linux 运维与 Python 后端方向，线上与线下结合的培训机构。",
    ),
    (
        "尚硅谷",
        "pxjg",
        0,
        "技术前沿",
        "大数据、Java 与前端方向的教研团队，配套源码与笔记。",
    ),
    ("北大计算机系", "gx", 0, "重点高校", "计算机学院公开课程，偏理论与算法基础。"),
    ("清华在线", "gx", 0, "重点高校", "继续教育学院推出的工程实践类公开课。"),
    ("沪江学院", "pxjg", 1, "语言加技术", "外语起家的综合教育机构，近年新增编程板块。"),
    ("独立讲师王雷", "gr", 1, "个人讲师", "十年大厂经验，独立开设架构与源码剖析课程。"),
]
orgs = []
for index, (name, category, city_index, tag, summary) in enumerate(ORG_PLAN):
    city = cities[city_index]
    orgs.append(
        CourseOrg.objects.create(
            name=name,
            category=category,
            city=city,
            tag=tag,
            address=f"{city.name}市{tag}路 {index + 1} 号",
            image=ORG_IMAGES[index % len(ORG_IMAGES)],
            click_num=60 - index * 5,
            desc=(
                f"<p>{summary}</p><h2>机构优势</h2><ul><li>实战项目驱动</li>"
                f"<li>讲师一对一答疑</li></ul><p>累计服务学员 {(index + 1) * 3200} 人。</p>"
            ),
            add_time=now - timedelta(days=40 - index),
        )
    )

TEACHER_PLAN = [
    ("沈志远", 12, "京东", "资深架构师", "深入浅出", 0),
    ("刘一航", 8, "字节跳动", "后端工程师", "案例丰富", 0),
    ("吴晓峰", 15, "阿里云", "技术专家", "体系完整", 1),
    ("周雅琴", 6, "网易", "前端负责人", "亲和力强", 2),
    ("郑凯文", 10, "腾讯", "高级经理", "重实践", 3),
    ("孙立平", 20, "华为", "首席工程师", "严谨", 3),
    ("何静", 5, "美团", "数据分析师", "细致", 6),
    ("黄博文", 9, "拼多多", "基础架构", "幽默", 7),
    ("林清玄", 7, "百度", "算法工程师", "推导详细", 4),
    ("徐克强", 14, "研究院", "研究员", "学术范", 5),
    ("马俊", 4, "短视频公司", "客户端工程师", "节奏快", 6),
    ("范冰", 11, "出行平台", "运维负责人", "干货多", 7),
]
teachers = []
for index, (name, years, company, position, points, org_index) in enumerate(
    TEACHER_PLAN
):
    teachers.append(
        Teacher.objects.create(
            org=orgs[org_index],
            name=name,
            age=28 + years,
            work_year=years,
            work_company=company,
            work_position=position,
            points=points,
            image=TEACHER_IMAGES[index % len(TEACHER_IMAGES)],
            click_num=50 - index * 3,
            add_time=now - timedelta(days=30 - index),
        )
    )

COURSE_PLAN = [
    ("Python 高级编程", "后端开发", "zj", "python", 240),
    ("Scrapy-Redis 分布式爬虫", "后端开发", "gj", "爬虫", 320),
    ("Django 入门到项目实战", "后端开发", "cj", "django", 400),
    ("Flask 微服务实战", "后端开发", "zj", "flask", 150),
    ("Python 数据挖掘实战", "数据分析", "zj", "数据分析", 500),
    ("Python3 深入系列", "后端开发", "gj", "python", 180),
    ("机器学习算法实践", "人工智能", "gj", "机器学习", 600),
    ("Java 高并发编程", "后端开发", "zj", "java", 300),
    ("Vue.js 全家桶开发", "前端开发", "cj", "前端", 260),
    ("React 新特性从0到1", "前端开发", "zj", "前端", 280),
    ("Linux 运维入门到精通", "运维", "cj", "linux", 210),
    ("Docker 与 K8s 微服务", "运维", "gj", "云原生", 190),
    ("MySQL 性能优化", "数据库", "zj", "mysql", 200),
    ("Redis 实战", "数据库", "cj", "redis", 170),
    ("数据结构与算法基础", "基础学科", "cj", "算法", 150),
    ("算法导论精读", "基础学科", "gj", "算法", 240),
    ("Go 语言并发编程", "后端开发", "zj", "golang", 220),
    ("大数据 Spark 实战", "数据分析", "gj", "大数据", 300),
]
LESSON_TITLES = ["基础", "进阶", "实战", "总结"]
courses = []
for index, (name, category, degree, tag, minutes) in enumerate(COURSE_PLAN):
    teacher = teachers[index % len(teachers)]
    lesson_count = 2 + index % 2
    course = Course.objects.create(
        course_org=teacher.org,
        teacher=teacher,
        name=name,
        category=category,
        degree=degree,
        tag=tag,
        desc=f"从实际遇到的问题出发，配合 {lesson_count} 个案例讲透 {tag}，学完可以直接上手做项目。",
        detail=(
            f"<p>本课程围绕 <strong>{name}</strong> 展开，先补齐概念，再用一个项目把知识点串起来。</p>"
            "<h2>你会学到什么</h2><ul><li>完整的知识地图</li><li>可复用的工程模板</li><li>常见坑与排查思路</li></ul>"
            "<p>下面是课程配套的项目结构示例：</p>"
            '<p><img src="/media/courses/2018/04/mysql.jpg" alt="项目示例"/></p>'
            "<p>课程资料下载在资源区，答疑在评论区进行。</p>"
        ),
        learn_times=minutes,
        students=random.randint(30, 300),
        click_nums=random.randint(80, 900),
        image=COURSE_IMAGES[index % len(COURSE_IMAGES)],
        is_banner=index in (0, 8),
        youneed_know="具备一门脚本语言的基础语法即可。",
        teacher_tell="跟着敲完所有示例，比看十遍视频有用。",
        add_time=now - timedelta(days=index),
    )
    for lesson_index in range(lesson_count):
        lesson = Lesson.objects.create(
            course=course,
            name=f"第 {lesson_index + 1} 章 {LESSON_TITLES[lesson_index]}",
        )
        for video_index in range(2):
            Video.objects.create(
                lesson=lesson,
                name=f"{lesson_index + 1}-{video_index + 1} 小节",
                learn_times=minutes // (lesson_count * 2),
                url=f"https://example.com/video/{index}.mp4",
            )
    courses.append(course)

for course in (courses[2], courses[3], courses[8], courses[12]):
    CourseResource.objects.create(
        course=course,
        name=f"{course.name} 源码与课件",
        download="course/resource/201804/media.zip",
    )

for index, (title, image, order) in enumerate(
    [
        ("夏季新课三折，限时一周", "banner/2018/05/57a801860001c34b12000460.jpg", 10),
        ("Django 实战训练营招生中", "banner/2018/05/57aa86a0000145c512000460.jpg", 20),
        (
            "机构入驻计划，流量扶持",
            "banner/2018/05/57a801860001c34b12000460_qEMt1Hg.jpg",
            30,
        ),
    ]
):
    Banner.objects.create(
        title=title,
        image=image,
        url="/course/list/",
        index=order,
        add_time=now - timedelta(days=index),
    )

# ---------------------------------------------------------------- 学习 / 收藏 / 评论 / 消息 / 咨询
for course in (courses[0], courses[2], courses[8], courses[11]):
    UserCourse.objects.create(user=student, course=course)
for course in (courses[1], courses[4]):
    UserCourse.objects.create(user=accounts["teacher01"], course=course)

for fav_type, target in [
    (1, courses[2]),
    (2, courses[0].course_org),
    (2, orgs[0]),
    (3, teachers[0]),
    (3, teachers[3]),
    (1, courses[8]),
]:
    UserFavorite.objects.create(user=student, fav_id=target.id, fav_type=fav_type)

for course, text in [
    (courses[0], "讲得挺细，跟着做完一遍收获很大。"),
    (courses[0], "希望能再加一章部署相关的内容。"),
    (courses[2], "入门友好，示例可以直接跑起来。"),
    (courses[8], "前端部分更新得很快。"),
    (courses[11], "容器编排那段反复看了三遍才懂。"),
]:
    CourseComments.objects.create(
        user=student,
        course=course,
        comments=text,
        add_time=now - timedelta(hours=random.randint(1, 72)),
    )

for text, read in [
    ("欢迎注册问渠在线，先去课程中心逛逛。", True),
    ("您收藏的《Django 入门到项目实战》更新了 2 个章节。", False),
    ("您在 2026 年完成了 3 门课程的学习。", True),
    ("《Docker 与 K8s 微服务》限时五折。", False),
    ("课程资料已上传，请到资源区下载。", False),
]:
    UserMessage.objects.create(
        user=student.id,
        message=text,
        has_read=read,
        add_time=now - timedelta(days=random.randint(0, 9)),
    )

for name, mobile, course_name in [
    ("张三", "13911112222", "Python 高级编程"),
    ("李四", "13922223333", "Vue.js 全家桶开发"),
    ("王五", "13933334444", "机器学习算法实践"),
]:
    UserAsk.objects.create(
        name=name,
        mobile=mobile,
        course_name=course_name,
        add_time=now - timedelta(days=random.randint(0, 5)),
    )

# ---------------------------------------------------------------- 让统计字段与真实数据一致
for course in Course.objects.all():
    course.fav_nums = UserFavorite.objects.filter(fav_type=1, fav_id=course.id).count()
    course.save(update_fields=["fav_nums"])
for teacher in Teacher.objects.all():
    teacher.fav_num = UserFavorite.objects.filter(fav_type=3, fav_id=teacher.id).count()
    teacher.save(update_fields=["fav_num"])
for org in CourseOrg.objects.all():
    org.fav_num = UserFavorite.objects.filter(fav_type=2, fav_id=org.id).count()
    org.course_nums = org.course_set.count()
    org.students = sum(org.course_set.values_list("students", flat=True))
    org.save(update_fields=["fav_num", "course_nums", "students"])

print("演示数据已生成：")
for label, model in [
    ("用户", UserProfile),
    ("城市", CityDict),
    ("机构", CourseOrg),
    ("讲师", Teacher),
    ("课程", Course),
    ("章节", Lesson),
    ("视频", Video),
    ("资源", CourseResource),
    ("首页轮播", Banner),
    ("收藏", UserFavorite),
    ("评论", CourseComments),
    ("消息", UserMessage),
    ("咨询", UserAsk),
]:
    print(f"  {label:6} {model.objects.count()}")
print(
    "后台账号 admin / admin123456    前台账号 student / student123456    未激活账号 newbie / newbie123456"
)
