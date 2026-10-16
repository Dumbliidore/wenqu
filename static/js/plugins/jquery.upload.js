jQuery.fn.extend({
    uploadPreview: function (opts) {
        $(this).each(function(){
             var _self = this,
                _this = $(this);
            opts = jQuery.extend({
                Img: "ImgPr",
                Width: 100,
                Height: 100,
                ImgType: ["gif", "jpeg", "jpg", "bmp", "png"],
                Callback: function () {}
            }, opts || {});
            _self.getObjectURL = function (file) {
                var url = null;
                if (window.createObjectURL != undefined) {
                    url = window.createObjectURL(file)
                } else if (window.URL != undefined) {
                    url = window.URL.createObjectURL(file)
                } else if (window.webkitURL != undefined) {
                    url = window.webkitURL.createObjectURL(file)
                }
                return url
            };
            _this.change(function () {
                if (this.value) {
                    if (!RegExp("\.(" + opts.ImgType.join("|") + ")$", "i").test(this.value.toLowerCase())) {
                        alert("选择文件错误,图片类型必须是" + opts.ImgType.join("，") + "中的一种");
                        this.value = "";
                        return false
                    }
                    var obj = _this.parent().siblings().children(opts.Img);
                    obj.attr('src', _self.getObjectURL(this.files[0]));
                    opts.Callback()
                }
            });
        });
    }
});
