(function () {
  "use strict";

  // unfold 在 load 时把 a.active 的 offsetTop 当成滚动容器内的偏移用，但容器的定位祖先
  // 是外层 fixed 的 #nav-sidebar，目标值因此多出侧栏头部的高度，靠下的项会被夹到 maxScroll
  // 边界；随后图标字体落地、内容高度微变，夹紧位置跟着回弹，视觉上就是上下抖。
  function settle() {
    var box = document.getElementById("nav-sidebar-apps");
    var active = box && box.querySelector("a.active");
    if (!active) {
      return;
    }

    var top = active.offsetTop - box.offsetTop;
    var needed = top - box.clientHeight + active.offsetHeight;
    var max = box.scrollHeight - box.clientHeight;
    var target = Math.max(0, Math.min(max, needed));

    // 只回拉过度滚动，不动用户自己滚上去的位置
    if (box.scrollTop > target) {
      box.scrollTop = target;
    }
  }

  // 用 rAF 保证排在 unfold 自己的 load 监听之后执行
  window.addEventListener("load", function () {
    requestAnimationFrame(settle);
  });

  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(function () {
      requestAnimationFrame(settle);
    });
  }
})();
