from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator


def paginate(request, queryset, per_page):
    """按 ?page= 取页；页码非法回落首页，超出范围回落末页。"""
    paginator = Paginator(queryset, per_page)

    try:
        return paginator.page(request.GET.get("page", 1))
    except PageNotAnInteger:
        return paginator.page(1)
    except EmptyPage:
        return paginator.page(paginator.num_pages)
