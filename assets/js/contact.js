/* Comfort Luxury Rides - quote form. Two submit paths, one result.
   Ported from MINA RANK/js/main.js (the audit form).

   No JS: a plain POST to Web3Forms. Native validation runs because `novalidate` is set from
   HERE and never in the markup. Web3Forms redirects back to /contact/?sent=1#sent and the
   :target rule in styles.css reveals the confirmation panel.

   JS: intercept, post the same FormData, reveal the same panel in place, never a dead button.
   Every string this script says comes off the form's data- attributes. If any hook is missing
   the block does not run and the native POST stands. */
(function () {
  "use strict";
  var wrap = document.getElementById("quote");
  var qf = document.getElementById("quote-form");

  if (wrap && /[?&]sent=1(&|$)/.test(window.location.search)) {
    wrap.classList.add("is-sent");
  }

  var doneEl = document.getElementById("sent");
  var say = document.getElementById("qf-say");
  var send = document.getElementById("qf-send");
  var sendText = document.getElementById("qf-send-text");
  var T_SENDING = qf && qf.getAttribute("data-sending");
  var T_SENDING_SAY = qf && qf.getAttribute("data-sending-say");
  var T_ERROR = qf && qf.getAttribute("data-error");

  if (qf && wrap && doneEl && say && send && sendText &&
      T_SENDING && T_SENDING_SAY && T_ERROR &&
      window.fetch && window.FormData && qf.checkValidity) {
    qf.setAttribute("novalidate", "novalidate");

    var sendLabel = sendText.textContent;
    var sending = false;

    var mark = function () {
      var req = qf.querySelectorAll("[required]");
      for (var i = 0; i < req.length; i++) {
        req[i].setAttribute("aria-invalid", req[i].checkValidity() ? "false" : "true");
      }
    };

    var settle = function (ok) {
      sending = false;
      send.disabled = false;
      sendText.textContent = sendLabel;
      if (ok) {
        say.classList.remove("is-err");
        say.textContent = "";
        wrap.classList.add("is-sent");
        doneEl.focus();
        if (doneEl.scrollIntoView) doneEl.scrollIntoView({ block: "start", behavior: "smooth" });
      } else {
        say.classList.add("is-err");
        say.textContent = T_ERROR;
        send.focus();
      }
    };

    qf.addEventListener("submit", function (e) {
      e.preventDefault();
      if (sending) return;

      /* honeypot: look sent, say nothing */
      var bot = qf.querySelector("[name=botcheck]");
      if (bot && bot.checked) { wrap.classList.add("is-sent"); return; }

      qf.classList.add("was-validated");
      mark();
      if (!qf.checkValidity()) {
        var bad = qf.querySelector(":invalid");
        if (bad) bad.focus();
        return;
      }

      sending = true;
      send.disabled = true;
      sendText.textContent = T_SENDING;
      say.classList.remove("is-err");
      say.textContent = T_SENDING_SAY;

      window.fetch(qf.getAttribute("action"), { method: "POST", body: new FormData(qf), headers: { Accept: "application/json" } })
        .then(function (r) { return r.json(); })
        .then(function (json) { settle(!!(json && json.success)); })
        .catch(function () { settle(false); });
    });

    qf.addEventListener("input", function (e) {
      if (qf.classList.contains("was-validated") && e.target.checkValidity) {
        e.target.setAttribute("aria-invalid", e.target.checkValidity() ? "false" : "true");
      }
    });
  }
})();
