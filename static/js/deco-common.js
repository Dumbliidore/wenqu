//顶部搜索栏搜索方法
function search_click(){
    var type = $('#jsSelectOption').attr('data-value'),
        keywords = encodeURIComponent($('#search_keywords').val()),
        request_url = '';
    if(keywords == ""){
        return
    }
    if(type == "course"){
        request_url = "/course/list?keywords="+keywords
    }else if(type == "teacher"){
        request_url = "/org/teacher/list?keywords="+keywords
    }else if(type == "org"){
        request_url = "/org/list?keywords="+keywords
    }
    window.location.href = request_url
}

$(function() {
    $(window).resize(function(){
        $('.dialogbox').each(function(){
            if($(this).css('display') == 'block'){
                centerDialog($(this));
            }
        });
    });
    $(".scrollLoading").scrollLoading();

    //右边悬浮按钮组
	$(window).scroll(function(){
		if($(window).scrollTop()>200){
			$('.sidebar').show();
		}else{
			$('.sidebar').hide();
		};
	});
	//返回顶部
	$('.totop').click(function(){
		$('html,body').animate({scrollTop:0},100);
		return false;
	});

    //顶部个人中心下拉框
    $('.header .personal').hover(function(){
        $('.header .userdetail').stop(true).show();
    },function(){
        $('.header .userdetail').stop(true).hide();
    });
    var msg_show = true,
        msg = +$('#MsgNum').text();
    function msgFlash(){
        var $elem = $('#MsgNum');
        if(!msg){
            clearInterval(m);
        }
        if(msg_show){
            $elem.text(msg);
            msg_show = false;
        }else{
            $elem.text('');
            msg_show = true;
        }
    }
    var m = setInterval(msgFlash,500);

    //顶部搜索栏搜索按钮事件
    $('#jsSelectOption').on('click', function(){
        var $jsSelectMenu = $('#jsSelectMenu');
        if($jsSelectMenu.css('display') == 'block') return;
        $jsSelectMenu.addClass('dis');
    });
    $('#jsSelectMenu > li').on('click', function(){
        var searchType = $(this).attr('data-value'),
            searchName = $(this).text(),
            $jsSelectOption = $('#jsSelectOption');
        $jsSelectOption.attr('data-value',searchType).text(searchName);
        $(this).parent().removeClass('dis');
    });
    $(document).on('click', function(e){
        if(e.target != $('#jsSelectOption')[0] && e.target != $('#jsSelectMenu')[0]){
            $('#jsSelectMenu').removeClass('dis');
        }
    });


    $('#jsSearchBtn').on('click',function(){
        search_click()
    });
    //搜索表单键盘事件
    $("#search_keywords").keydown(function(event){
        if(event.keyCode == 13){
             $('#jsSearchBtn').trigger('click');
        }
    });

    //input的focus和blur效果
	$('.dialogbox .box input').focus(function(){
		$(this).parent('.box').removeClass().addClass('box focus');
	});
	$('.dialogbox .box input').blur(function(){
		$(this).parent('.box').removeClass().addClass('box blur');
	});

    //弹出框关闭按钮
	$('.jsCloseDialog').on('click', function(){
        $('#jsDialog').hide();
        $('html').removeClass('dialog-open');
		$(this).parents('.dialogbox').hide();
        $('#dialogBg').hide();
        if($(this).parent().find('form')[0]){
            $(this).parent().find('form')[0].reset();
        }
	});

	/*列表更多按钮*/
    $('.listoptions').find('.more').click(function(){
        var height = $('.listoptions .cont').height();
        if(!$('.listoptions .cont').hasClass("opened")){
            $('.listoptions .cont').css({
                "height":"auto",
                "overflow":"visible"
            }).addClass("opened");
            $('.listoptions').find('.more').html('收起')
        }else{

            $('.listoptions .cont').css({
                "height":"50px",
                "overflow":"hidden"
            }).removeClass("opened");

            $('.listoptions').find('.more').html('更多')
        }
    });

    $('img').on('error', function(){
        $(this).off('error').attr('src', '/static/images/error-img.png');
    });
});
