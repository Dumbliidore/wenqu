from operation.models import UserFavorite


def is_faved(request, fav_id, fav_type):
    """收藏按钮的初始状态；未登录一律按未收藏处理。"""
    if not request.user.is_authenticated:
        return False
    return UserFavorite.objects.filter(
        user=request.user, fav_id=fav_id, fav_type=fav_type
    ).exists()
