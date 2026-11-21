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

  // Time-limited sale: shows only until the date in data-sale-until, then the
  // page falls back to the regular prices on its own.
  var saleOn = false;
  document.querySelectorAll("[data-sale-until]").forEach(function (el) {
    var until = Date.parse(el.getAttribute("data-sale-until"));
    if (!isNaN(until) && Date.now() < until) { el.hidden = false; saleOn = true; }
  });
  if (saleOn) {
    document.querySelectorAll("[data-sale]").forEach(function (td) {
      var full = td.textContent.replace(/\s*USD\s*$/, "");
      td.innerHTML = '<s class="was">' + full + '</s> ' + td.getAttribute("data-sale") + " USD";
    });
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
  // Opening slideshow: crossfade every few seconds, loading each photo just before it shows
  var show = document.querySelector("[data-slides]");
  var still = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (show && !still) {
    var phone = window.matchMedia("(max-width: 760px)");
    var all = Array.prototype.slice.call(show.querySelectorAll(".slide"));
    var pauseBtn = document.querySelector(".slides-pause");
    var timer = null, paused = false;
    var load = function (pic, done) {
      var img = pic.querySelector("img");
      if (img.hasAttribute("data-src")) {
        pic.querySelectorAll("[data-srcset]").forEach(function (s) { s.srcset = s.getAttribute("data-srcset"); s.removeAttribute("data-srcset"); });
        img.src = img.getAttribute("data-src");
        img.removeAttribute("data-src");
      }
      if (!done) return;
      if (img.complete && img.naturalWidth) done();
      else { img.addEventListener("load", done, { once: true }); img.addEventListener("error", done, { once: true }); }
    };
    var usable = function () {
      return all.filter(function (p) { return !(phone.matches && p.classList.contains("desk-only")); });
    };
    var next = function () {
      var list = usable();
      var cur = show.querySelector(".slide.is-on");
      var i = list.indexOf(cur);
      var nxt = list[(i + 1) % list.length];
      if (!nxt || nxt === cur) return;
      load(nxt, function () {
        if (paused || document.hidden) return;
        if (cur) cur.classList.remove("is-on");
        nxt.classList.add("is-on");
        load(list[(list.indexOf(nxt) + 1) % list.length]);
      });
    };
    var start = function () { if (!timer && !paused) timer = setInterval(next, 6500); };
    var stop = function () { clearInterval(timer); timer = null; };
    if (all.length > 1) {
      window.addEventListener("load", function () { load(usable()[1] || all[1]); });
      start();
      document.addEventListener("visibilitychange", function () { if (document.hidden) stop(); else start(); });
      if (pauseBtn) {
        pauseBtn.hidden = false;
        pauseBtn.addEventListener("click", function () {
          paused = !paused;
          pauseBtn.setAttribute("aria-pressed", paused ? "true" : "false");
          pauseBtn.setAttribute("aria-label", paused ? "Play the photos" : "Pause the photos");
          if (paused) stop(); else start();
        });
      }
    }
  }

  // Telegram buttons that copy a ready-made message first (Telegram links can't carry it)
  document.querySelectorAll("[data-copy-msg]").forEach(function (a) {
    a.addEventListener("click", function () {
      var msg;
      if (a.getAttribute("data-copy-msg") === "picks") {
        var box = a.closest("[data-picks]");
        var picked = Array.prototype.map.call(box.querySelectorAll("input:checked"), function (i) { return "- " + i.value; });
        msg = picked.length ? "Hi Electra, I'd love some help. This sounds like me:\n" + picked.join("\n")
                            : "Hi Electra, I'd love some help with my content business.";
      } else {
        msg = "Hi Electra, please add me to the Creator Lounge. A little about what I make: ";
      }
      var note = a.closest(".card").querySelector(".pick-note");
      var done = function (ok) {
        if (note) note.textContent = ok ? "Copied. Paste it into the chat on Telegram." : "Tell me what you ticked when the chat opens.";
      };
      try { navigator.clipboard.writeText(msg).then(function () { done(true); }, function () { done(false); }); }
      catch (e) { done(false); }
    });
  });

  // Countdown timers: "3d 07h 12m 05s left", hidden once the time is up
  document.querySelectorAll("[data-countdown]").forEach(function (el) {
    var end = Date.parse(el.getAttribute("data-countdown"));
    if (isNaN(end)) return;
    var box = el.closest("[data-sale-until]") || el;
    var pad = function (n) { return (n < 10 ? "0" : "") + n; };
    var tick = function () {
      var left = Math.floor((end - Date.now()) / 1000);
      if (left <= 0) { box.hidden = true; clearInterval(t); return; }
      var d = Math.floor(left / 86400), h = Math.floor(left % 86400 / 3600), m = Math.floor(left % 3600 / 60), sec = left % 60;
      el.innerHTML = '<span>' + d + '<small>d</small></span><span>' + pad(h) + '<small>h</small></span><span>' + pad(m) +
        '<small>m</small></span><span>' + pad(sec) + '<small>s</small></span> <em>left</em>';
    };
    var t = setInterval(tick, 1000);
    tick();
  });

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
