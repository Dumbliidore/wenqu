//刷新验证码
function refresh_captcha(event){
    $.get("/captcha/refresh/?"+Math.random(), function(result){
        $('#'+event.data.form_id+' .captcha').attr("src",result.image_url);
        $('#id_captcha_0').attr("value",result.key);
    });
    return false;
}

$(function() {
    var unslider = $('.imgslide').unslider({
        speed: 500,
        delay: 3000,
        complete: function() {},
        keys: true,
        dots: true,
        fluid: false
    });
    $('.unslider-arrow').click(function() {
        var fn = this.className.split(' ')[1];
        unslider.data('unslider')[fn]();
    });

    $('.tab > h2').click(function(){
        var _self = $(this),
            index = _self.index();
        _self.addClass('active').siblings().removeClass('active');
        $('.tab-form').eq(index).removeClass('hide').siblings('.tab-form').addClass('hide');
    });

    //input的focus和blur效果
	$('input[type=text]').focus(function(){
		$(this).parent().removeClass('blur').addClass('focus');
	});
	$('input[type=text]').blur(function(){
		$(this).parent().removeClass('focus').addClass('blur');
	});
	$('input[type=password]').focus(function(){
		$(this).parent().removeClass('blur').addClass('focus');
	});
	$('input[type=password]').blur(function(){
		$(this).parent().removeClass('focus').addClass('blur');
	});

    //注册、找回密码页验证码点击刷新
    $('#email_register_form .captcha').click({'form_id':'email_register_form'},refresh_captcha);
    $('#jsFindPwdForm .captcha').click({'form_id':'jsFindPwdForm'},refresh_captcha);
});
