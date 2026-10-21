$(function() {
    /*首页轮播：unslider 会把 .imgslide 定成第一张图的尺寸，箭头靠类名第二个词调 prev/next*/
    var unslider = $('.imgslide').unslider({
        speed: 500,
        delay: 5000,
        keys: true,
        dots: true,
        fluid: false
    });
    $('.unslider-arrow').click(function() {
        var fn = this.className.split(' ')[1];
        unslider.data('unslider')[fn]();
    });
});
