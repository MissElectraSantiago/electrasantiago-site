(function () {
  "use strict";

  // Mobile menu
  var btn = document.querySelector(".menu-btn");
  var nav = document.getElementById("site-nav");
  if (btn && nav) {
    btn.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      btn.setAttribute("aria-expanded", open ? "true" : "false");
      btn.textContent = open ? "Close" : "Menu";
    });
  }

  // 18+ notice: shown once per browser
  var KEY = "es-age-ok";
  var gate = document.getElementById("age-gate");
  var ok = false;
  try { ok = localStorage.getItem(KEY) === "1"; } catch (e) {}
  if (!ok) { try { ok = sessionStorage.getItem(KEY) === "1"; } catch (e) {} }
  if (gate && !ok) {
    gate.hidden = false;
    var enter = document.getElementById("age-enter");
    if (enter) {
      enter.focus();
      enter.addEventListener("click", function () {
        try { localStorage.setItem(KEY, "1"); } catch (e) {}
        try { sessionStorage.setItem(KEY, "1"); } catch (e) {}
        gate.hidden = true;
      });
    }
  }

  // Copy buttons on the creator resources page
  document.querySelectorAll("[data-copy]").forEach(function (b) {
    b.addEventListener("click", function () {
      var src = document.getElementById(b.getAttribute("data-copy"));
      if (!src) return;
      var text = src.innerText.trim();
      var done = function () { var t = b.textContent; b.textContent = "Copied"; setTimeout(function () { b.textContent = t; }, 1600); };
      var fallback = function () {
        var r = document.createRange(); r.selectNodeContents(src);
        var s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
        b.textContent = "Selected, press copy";
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, fallback);
      } else { fallback(); }
    });
  });

  // Forms. Each form posts to the address in data-endpoint (a form service such as
  // Formspree). Until an endpoint is set, the form says so instead of failing silently.
  document.querySelectorAll("form[data-form]").forEach(function (f) {
    f.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var status = f.querySelector(".form-status");
      var endpoint = f.getAttribute("data-endpoint");
      if (!endpoint) {
        if (status) status.textContent = "This form isn't connected yet. Message me on Telegram in the meantime.";
        return;
      }
      if (status) status.textContent = "Sending…";
      fetch(endpoint, { method: "POST", body: new FormData(f), headers: { Accept: "application/json" } })
        .then(function (r) {
          if (!r.ok) throw new Error();
          f.reset();
          if (status) status.textContent = f.getAttribute("data-success") || "Received.";
        })
        .catch(function () { if (status) status.textContent = "That didn't go through. Try again, or reach me on Telegram."; });
    });
  });
})();
