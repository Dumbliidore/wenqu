// 登录族四页的脚本。原来这里还有轮播初始化和 tab 切换，两块的标记都随页面改版删掉了；
// 输入框的 focus/blur 高亮改由 CSS 的 :focus-within 负责，也不再需要绑类名。
$(function () {
    // 点击验证码换一张：图片地址和隐藏域里的 key 要一起换，
    // 只换图片的话提交时校验的还是旧那一张。
    $('.captcha').on('click', function () {
        var img = $(this);
        $.get('/captcha/refresh/?' + Math.random(), function (result) {
            img.attr('src', result.image_url);
            $('#id_captcha_0').attr('value', result.key);
        });
        return false;
    });
});
