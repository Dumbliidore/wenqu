function centerDialog(dialogBox){
    $(dialogBox).show(0,function(){
        var winHei = $(window).height(),
        dialogHei = $(this).height();
        if(dialogHei + 120 < winHei){
            $(this).css('margin-top',(winHei-dialogHei)/2 + 'px');
            $('html').removeClass('dialog-open');
        }else{
             $(this).css('margin-top','30px');
            $('html').addClass('dialog-open');
        }
    });
}
var Dml = {};
    Dml.fun = {
        showErrorTips: function($elem,tips){
            $elem.html(tips).show();
            return false;
        },
        showDialog: function(dialogBox){
            $('#jsDialog').show();
            $('#dialogBg').show();
            $('.dialogbox').hide();
           centerDialog(dialogBox);
            if(arguments[1]) $(arguments[1]).hide();
            if(arguments[2]) $(arguments[2]).hide();
        },
        showTipsDialog: function(obj){
            //type :'' || failbox
            var $Box = $('#jsSuccessTips'),
                h1 = obj.title || '提示',
                h2 = obj.h2 || '您的操作成功！';
                p = obj.p || '';
                type = obj.type || '';
            $('#jsDialog').show();
            $('#dialogBg').show();
            $('.dialogbox').hide();
            $Box.find('h1').html(h1);
            $Box.find('h2').html(h2);
            $Box.find('p').html(p);
            if(type){
                $Box.addClass(type);
                centerDialog($Box);
            }else{
                $Box.removeClass('failbox');
                centerDialog($Box);
            }
        },
        showValidateError: function($elem,tips){
            var $tips = arguments[2] || '';
            $elem.focus();
            setTimeout(function(){
                $elem.parent().addClass('errorput');
                if($tips){
                    $tips.html(tips).show();
                }else{
                    if($elem.attr('id') == 'mobile-register-captcha_1'){
                        $('#jsMobileTips').html(tips).show();
                    }else if($elem.attr('id') == 'jsPhoneRegCaptcha'){
                        $elem.parent().siblings('.error').html(tips).show();
                    }else{
                        $elem.parent().siblings('.error').html(tips).show();
                    }
                }
            },10);
            return false;
        },
        getDate: function(){
            if (arguments[0]){
                var now = new Date(arguments[0])
            }else{
                var now = new Date();
            }

            return now.getFullYear() + '-' + (now.getMonth()+1) + '-' + now.getDate();
        },
        winReload: function(){
            var URL = arguments[0] || window.location.href;
            setTimeout(function(){
                window.location.href = URL;
            },1500);
        }
    };
    Dml.regExp = {
        phone: /^1([38]\d|4[57]|5[0-35-9]|7[06-8]|8[89])\d{8}$/,
        tel:/(^1([38]\d|4[57]|5[0-35-9]|7[06-8]|8[89])\d{8}$)|(^((\d{7,8})|(\d{4}|\d{3})-(\d{7,8})|(\d{4}|\d{3})-(\d{7,8})-(\d{4}|\d{3}|\d{2}|\d{1})|(\d{7,8})-(\d{4}|\d{3}|\d{2}|\d{1}))$)/,
        email: /^([a-zA-Z0-9_-])+@([a-zA-Z0-9_-])+(.[a-zA-Z0-9_-])+/,
        phMail: /(^1([38]\d|4[57]|5[0-35-9]|7[06-8]|8[89])\d{8}$)|(^([a-zA-Z0-9_-])+@([a-zA-Z0-9_-])+(.[a-zA-Z0-9_-])+)/,
        number: /^[0-9]*$/,
        float: /^\d+(\.\d+)?$/,
        zsNumber: /^(-?[1-9]\d*|0)$/,
        name: /^[\u4e00-\u9fa5a-zA-Z]+$/,
        pwd: /^([^\u4e00-\u9fa5]{6,20})$/,
        verifyCode: /^[a-zA-z]{5}$/,
        phoneCode: /^\d{6}$/,
        emailCode: /^\d{4}$/,
        rsiName: /^[\u4e00-\u9fa5\-a-zA-Z0-9]{2,30}$/,
        idCard: /(^\d{15}$)|(^\d{18}$)|(^\d{17}(\d|X|x)$)/
    };
    Dml.Msg = {
        epUserName: '请输入登录手机或邮箱！',
        erUserName: '请输入正确的登录手机或邮箱！',
        epPhone: '请输入您的手机号码！',
        erPhone: '请输入正确的手机号码！',
        epTel: '请输入您的电话号码！',
        erTel: '请输入正确的电话号码，固定电话：区号-号码！',
        epVerifyCode: '请输入验证码！',
        erVerifyCode: '请输入正确的验证码！',
        epMail: '请输入您的邮箱！',
        erMail: '请输入正确的邮箱！',
        epPwd: '请输入登录密码！',
        erPwd: '密码为6-20位非中文字符！',
        epResetPwd: '请输入密码！',
        erResetPwd: '密码为6-20位非中文字符！',
        epRePwd:'请重复输入密码！',
        erRePwd:'两次密码输入不一致！',
        epPhCode: '请输入手机验证码！',
        erPhCode: '请输入正确的手机验证码！',
        epEmCode: '请输入邮箱验证码！',
        erEmCode: '请输入正确的邮箱验证码！',
        epName: '请输入您的姓名！',
        epNickName: '请输入昵称！',
    };
