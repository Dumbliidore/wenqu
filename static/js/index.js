$(function() {
	/*index*/
	$('.module3 .company').hover(function(){
		$(this).find('.score').stop(true,true).fadeToggle(200);
	});

	/*banner imgslide*/
    var unslider = $('.imgslide').unslider({
		speed: 500,               //  The speed to animate each slide (in milliseconds)
		delay: 5000,              //  The delay between slide animations (in milliseconds)
		complete: function() {},  //  A function that gets called after every slide animation
		keys: true,               //  Enable keyboard (left, right) arrow shortcuts
		dots: true,               //  Display dot navigation
		fluid: false              //  Support responsive design. May break non-responsive designs
	});
    $('.unslider-arrow').click(function() {
        var fn = this.className.split(' ')[1];
        unslider.data('unslider')[fn]();
    });

    var unslider2 = $('.imgslide2').unslider({
		speed: 500,
		complete: function() {},
		keys: true,
		dots: false,
		fluid: false
	});
    $('.unslider-arrow2').click(function() {
        var fn = this.className.split(' ')[1];
        unslider2.data('unslider')[fn]();
    });
});
