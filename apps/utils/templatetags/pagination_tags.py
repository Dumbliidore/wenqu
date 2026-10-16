"""分页相关的模板标签，取代已停止维护的 pure_pagination。"""

from django import template
from django.utils.http import urlencode

register = template.Library()


@register.simple_tag(takes_context=True)
def page_url(context, page):
    """保留当前筛选/排序参数，只把 page 换成指定页码。"""
    request = context.get("request")
    if request is None:
        return ""

    params = request.GET.dict()
    params.pop("page", None)
    params["page"] = page
    return urlencode(params)


@register.filter(name="page_numbers")
def page_numbers(page_obj, on_each_side=3):
    """页码序列，两端溢出由分页器插入省略号（值为分页器的 ELLIPSIS）。"""
    return page_obj.paginator.get_elided_page_range(
        page_obj.number, on_each_side=on_each_side, on_ends=1
    )
