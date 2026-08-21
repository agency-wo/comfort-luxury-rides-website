/* Comfort Luxury Rides - global interactions: header, mobile nav, scroll reveal, WhatsApp FAB, back to top.
   Ported from MBC SRL/assets/js/main.js (scroll lock, nav, reveal, FAB) and re-namespaced. */
(function () {
  "use strict";
  var header = document.querySelector(".site-header");

  /* Scroll lock, shared with the gallery lightbox.
     overflow:hidden alone lets iOS Safari rubber-band the page behind a fullscreen overlay and
     drops the offset, so pin the body and restore it on release. Depth-counted so two overlays
     can never unlock each other early. */
  var lockDepth = 0, lockY = 0;
  function lockScroll() {
    if (lockDepth++) return;
    lockY = Math.round(window.scrollY || window.pageYOffset || 0);
    var s = document.body.style;
    s.position = "fixed"; s.top = -lockY + "px"; s.left = "0"; s.right = "0";
  }
  function unlockScroll() {
    if (!lockDepth || --lockDepth) return;
    var s = document.body.style;
    s.position = ""; s.top = ""; s.left = ""; s.right = "";
    var d = document.documentElement, prev = d.style.scrollBehavior;
    d.style.scrollBehavior = "auto";
    window.scrollTo(0, lockY);
    d.style.scrollBehavior = prev;
  }
  window.CLR = window.CLR || {};
  window.CLR.lockScroll = lockScroll;
  window.CLR.unlockScroll = unlockScroll;

  /* Header solid state after a short scroll */
  function onScroll() {
    if (!header || lockDepth) return; /* body is pinned: scrollY reads 0 */
    if (window.scrollY > 40) header.classList.add("is-solid");
    else header.classList.remove("is-solid");
  }
  if (header) {
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  /* Mobile navigation */
  var toggle = document.querySelector(".nav-toggle");
  var menu = document.querySelector(".nav-menu");
  function closeNav() {
    if (!document.body.classList.contains("nav-open")) return;
    document.body.classList.remove("nav-open");
    unlockScroll();
    if (toggle) { toggle.setAttribute("aria-expanded", "false"); toggle.setAttribute("aria-label", "Open menu"); }
  }
  if (toggle && menu) {
    toggle.addEventListener("click", function () {
      var open = document.body.classList.toggle("nav-open");
      if (open) lockScroll(); else unlockScroll();
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
      if (open) { var f = menu.querySelector("a"); if (f) f.focus(); }
    });
    menu.querySelectorAll("a").forEach(function (a) { a.addEventListener("click", closeNav); });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && document.body.classList.contains("nav-open")) { closeNav(); if (toggle) toggle.focus(); }
    });
    window.addEventListener("resize", function () { if (window.innerWidth > 860) closeNav(); });
  }

  /* Scroll reveal: IntersectionObserver primary, scroll-idle sweep as a safety net
     (intersection callbacks can be outrun by instant or programmatic jumps). */
  var reveals = Array.prototype.slice.call(document.querySelectorAll(".reveal"));
  if (reveals.length) {
    function revealCheck(stagger) {
      var vh = window.innerHeight || document.documentElement.clientHeight;
      var hit = [], rest = [];
      for (var i = 0; i < reveals.length; i++) {
        (reveals[i].getBoundingClientRect().top < vh * 0.92 ? hit : rest).push(reveals[i]);
      }
      reveals = rest;
      var seen = new Map();
      for (var j = 0; j < hit.length; j++) {
        var par = hit[j].parentNode, k = seen.get(par) || 0;
        seen.set(par, k + 1);
        if (stagger === true) hit[j].style.setProperty("--d", Math.min(k, 3) * 80 + "ms");
        hit[j].classList.add("is-visible");
      }
    }
    if ("IntersectionObserver" in window) {
      var io = new IntersectionObserver(function (entries) {
        var seen = new Map();
        for (var i = 0; i < entries.length; i++) {
          if (!entries[i].isIntersecting) continue;
          var el = entries[i].target, par = el.parentNode, k = seen.get(par) || 0;
          seen.set(par, k + 1);
          el.style.setProperty("--d", Math.min(k, 3) * 80 + "ms");
          el.classList.add("is-visible");
          io.unobserve(el);
          var idx = reveals.indexOf(el);
          if (idx > -1) reveals.splice(idx, 1);
        }
      }, { rootMargin: "0px 0px -8% 0px", threshold: 0 });
      for (var n = 0; n < reveals.length; n++) io.observe(reveals[n]);
      var idle;
      window.addEventListener("scroll", function () {
        clearTimeout(idle);
        if (reveals.length) idle = setTimeout(function () { revealCheck(true); }, 250);
      }, { passive: true });
      window.addEventListener("load", function () { if (reveals.length) revealCheck(); });
    } else {
      window.addEventListener("load", revealCheck);
      requestAnimationFrame(function () { revealCheck(); });
    }
  }

  /* WhatsApp FAB: visible only when no in-layout contact CTA is on screen.
     Suppressors: hero buttons, CTA band, contact card, footer. Not tied to scroll position. */
  var fab = document.querySelector(".wa-fab");
  if (fab) {
    var blockers = document.querySelectorAll(".hero__btns, .cta-band, .contact-card, .site-footer");
    if (!("IntersectionObserver" in window) || !blockers.length) {
      fab.classList.add("is-in");
    } else {
      var waIo = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) { e.target.__hit = e.isIntersecting; });
        var blocked = false;
        blockers.forEach(function (el) { if (el.__hit) blocked = true; });
        fab.classList.toggle("is-in", !blocked);
      }, { threshold: 0 });
      blockers.forEach(function (el) { waIo.observe(el); });
    }
  }

  /* Back to top: shown once the hero has scrolled out (IntersectionObserver sentinel, no scroll math) */
  var toTop = document.querySelector(".to-top");
  var hero = document.querySelector(".hero");
  if (toTop && hero && "IntersectionObserver" in window) {
    new IntersectionObserver(function (entries) {
      toTop.classList.toggle("is-in", !entries[0].isIntersecting);
    }, { threshold: 0 }).observe(hero);
    toTop.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: "smooth" });
      var first = document.querySelector(".skip-link"); if (first) first.focus({ preventScroll: true });
    });
  }

  /* Footer year */
  var y = document.querySelector("[data-year]");
  if (y) y.textContent = new Date().getFullYear();
})();
