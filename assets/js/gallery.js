/* Comfort Luxury Rides - fleet gallery: accessible lightbox (keyboard, focus trap, swipe, neighbour preload).
   Ported from MBC SRL/assets/js/gallery.js, category filters removed (one category). */
(function () {
  "use strict";
  var grid = document.querySelector("[data-gallery]");
  if (!grid) return;
  var items = Array.prototype.slice.call(grid.querySelectorAll(".gallery-item"));
  var lb = document.querySelector(".lightbox");
  if (!lb || !items.length) return;
  var lbImg = lb.querySelector(".lightbox__img");
  var lbCap = lb.querySelector(".lightbox__cap");
  var current = 0, lastFocus = null;

  function fullSrc(fig) {
    if (window.innerWidth < 700) {
      var m = fig.getAttribute("data-full-m");
      if (m) return m;
    }
    return fig.getAttribute("data-full");
  }
  function show(i) {
    current = (i + items.length) % items.length;
    var fig = items[current];
    lbImg.src = fullSrc(fig);
    lbImg.alt = fig.querySelector("img").alt;
    lbCap.textContent = fig.querySelector("img").alt;
    [current + 1, current - 1].forEach(function (n) {
      var f = items[(n + items.length) % items.length];
      if (f) { var im = new Image(); im.src = fullSrc(f); }
    });
  }
  function open(fig) {
    lastFocus = document.activeElement;
    show(items.indexOf(fig));
    lb.classList.add("is-open");
    lb.setAttribute("aria-hidden", "false");
    document.body.classList.add("lb-open");
    if (window.CLR) window.CLR.lockScroll(); else document.body.style.overflow = "hidden";
    lb.querySelector(".lb-close").focus();
  }
  function close() {
    lb.classList.remove("is-open");
    lb.setAttribute("aria-hidden", "true");
    document.body.classList.remove("lb-open");
    if (window.CLR) window.CLR.unlockScroll(); else document.body.style.overflow = "";
    if (lastFocus) lastFocus.focus();
  }
  items.forEach(function (fig) {
    fig.addEventListener("click", function () { open(fig); });
    fig.setAttribute("tabindex", "0");
    fig.setAttribute("role", "button");
    fig.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(fig); }
    });
  });
  lb.querySelector(".lb-close").addEventListener("click", close);
  lb.querySelector(".lb-next").addEventListener("click", function () { show(current + 1); });
  lb.querySelector(".lb-prev").addEventListener("click", function () { show(current - 1); });
  lb.addEventListener("click", function (e) { if (e.target === lb) close(); });
  document.addEventListener("keydown", function (e) {
    if (!lb.classList.contains("is-open")) return;
    if (e.key === "Escape") close();
    else if (e.key === "ArrowRight") show(current + 1);
    else if (e.key === "ArrowLeft") show(current - 1);
    else if (e.key === "Tab") {
      var f = lb.querySelectorAll("button");
      var first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });
  var touchX = null;
  lb.addEventListener("touchstart", function (e) { touchX = e.changedTouches[0].clientX; }, { passive: true });
  lb.addEventListener("touchend", function (e) {
    if (touchX === null) return;
    var dx = e.changedTouches[0].clientX - touchX;
    if (Math.abs(dx) > 40) show(dx < 0 ? current + 1 : current - 1);
    touchX = null;
  }, { passive: true });
})();
