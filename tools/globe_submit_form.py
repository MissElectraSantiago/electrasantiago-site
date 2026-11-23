"""The globe's "Submit your event / label" button opens a short form on the page.

Until 23 Nov 2026 the button pointed at a Jotform link that was never added, so
it did nothing useful (an Austin events group wrote in to say so). Now it opens
a form that sends the details to Electra through the site's own send-note.php,
the same way the "Send a note" box does. Used by tools/patch_globe.py.
"""

CSS_AFTER = '.esg-hp { position: absolute !important; left: -9999px; width: 1px; height: 1px; opacity: 0; }'
CSS = '''
.esg-sub-form { flex: 1 1 100%; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px 20px; padding-top: 8px; }
.esg-sub-form[hidden], .esg-sub-field[hidden] { display: none; }
.esg-sub-field { display: grid; gap: 6px; min-width: 0; font-size: 14px; color: var(--ink-soft); }
.esg-sub-field input, .esg-sub-field textarea { width: 100%; box-sizing: border-box; height: 44px; padding: 0 16px; border: 1px solid var(--ink); border-radius: 999px; background: var(--paper); color: var(--ink); font: inherit; }
.esg-sub-field textarea { height: auto; min-height: 100px; padding: 12px 16px; border-radius: 18px; resize: vertical; }
.esg-sub-field ::placeholder { color: var(--ink-soft); }
.esg-sub-wide { grid-column: 1 / -1; }
@media (max-width: 560px) { .esg-sub-form { grid-template-columns: 1fr; } .esg-sub-form .esg-cta { width: 100%; } }'''

HTML_OLD = '''        <a class="esg-cta" id="esg-submit" href="#" target="_blank" rel="noopener">Submit your event</a>
        <p class="esg-cta-note" id="esg-submit-note" hidden></p>
      </div>
'''
HTML_NEW = '''        <a class="esg-cta" id="esg-submit" href="#" target="_blank" rel="noopener" aria-controls="esg-sub-form" aria-expanded="false">Submit your event</a>
        <p class="esg-cta-note" id="esg-submit-note" hidden></p>
      </div>
      <form class="esg-sub-form" id="esg-sub-form" novalidate hidden>
        <label class="esg-sub-field"><span id="esg-sf-name-l">Event name</span><input id="esg-sf-name" maxlength="120" required></label>
        <label class="esg-sub-field"><span>City and country</span><input id="esg-sf-city" maxlength="120" required></label>
        <label class="esg-sub-field" id="esg-sf-dates-w"><span>Dates</span><input id="esg-sf-dates" maxlength="120" placeholder="For example 14 to 16 May 2027"></label>
        <label class="esg-sub-field"><span>Website or social link</span><input id="esg-sf-url" type="url" maxlength="300" placeholder="https://"></label>
        <label class="esg-sub-field esg-sub-wide"><span id="esg-sf-about-l">About it</span><textarea id="esg-sf-about" maxlength="1000"></textarea></label>
        <label class="esg-sub-field esg-sub-wide"><span>Your email, so Electra can reply</span><input id="esg-sf-email" type="email" autocomplete="email" maxlength="200" required></label>
        <input class="esg-hp" type="text" name="_gotcha" tabindex="-1" autocomplete="off" aria-hidden="true">
        <div class="esg-sub-wide"><button class="esg-cta" type="submit" id="esg-sf-send">Send for review</button><p class="esg-cta-note" id="esg-sf-note" role="status" hidden></p></div>
      </form>
'''

JS_OLD = '''    var a = $("esg-submit");
    a.addEventListener("click", function (ev) {
      var url = mode === "fashion" ? SUBMIT_URL_FASHION : SUBMIT_URL;
      if (/^https:\\/\\//.test(url)) { a.href = url; return; }
      {
        ev.preventDefault();
        var n = $("esg-submit-note");
        n.textContent = "Your Jotform form opens here once its link is added.";
        n.hidden = false;
      }
    });
  })();'''
JS_NEW = '''    var a = $("esg-submit"), form = $("esg-sub-form"), note = $("esg-sf-note"), send = $("esg-sf-send");
    function f(id) { return $("esg-sf-" + id); }
    function say(t) { note.textContent = t; note.hidden = false; }
    a.addEventListener("click", function (ev) {
      var url = mode === "fashion" ? SUBMIT_URL_FASHION : SUBMIT_URL;
      if (/^https:\\/\\//.test(url)) { a.href = url; return; }
      ev.preventDefault();
      form.hidden = !form.hidden;
      a.setAttribute("aria-expanded", String(!form.hidden));
      if (!form.hidden) f("name").focus();
    });
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      if (form.elements._gotcha.value) return;
      var fashion = mode === "fashion";
      var name = f("name").value.trim(), city = f("city").value.trim(), mail = f("email").value.trim();
      var dates = f("dates").value.trim(), link = f("url").value.trim(), about = f("about").value.trim();
      if (!name) { say(fashion ? "Add your label's name." : "Add the event's name."); f("name").focus(); return; }
      if (!city) { say("Add the city and country."); f("city").focus(); return; }
      if (!/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(mail)) { say("Add your email so Electra can reply."); f("email").focus(); return; }
      var lines = [(fashion ? "Label: " : "Event: ") + name, "Where: " + city];
      if (!fashion && dates) lines.push("Dates: " + dates);
      if (link) lines.push("Link: " + link);
      if (about) lines.push("", about);
      var fd = new FormData();
      fd.append("message", lines.join("\\n")); fd.append("email", mail); fd.append("view", mode);
      fd.append("page", (fashion ? "Label submission: " : "Event submission: ") + name);
      send.disabled = true; say("Sending...");
      fetch(SUGGEST_URL, { method: "POST", body: fd, headers: { Accept: "application/json" } })
        .then(function (r) { if (!r.ok) throw new Error(r.status); form.reset(); say("Thank you. Your " + (fashion ? "label" : "event") + " is on its way to Electra for review."); })
        .catch(function () { say("That didn't send. Please try again in a moment."); })
        .then(function () { send.disabled = false; });
    });
  })();'''

MODE_OLD = '$("esg-submit-note").hidden = true;'
MODE_NEW = ('$("esg-submit-note").hidden = true; $("esg-sf-note").hidden = true;\n'
            '    $("esg-sf-name-l").textContent = m === "fashion" ? "Label name" : "Event name";\n'
            '    $("esg-sf-about-l").textContent = m === "fashion" ? "What you make" : "About it";\n'
            '    $("esg-sf-dates-w").hidden = m === "fashion";')


def apply(html):
    if 'id="esg-sub-form"' in html:
        return html
    for old in (CSS_AFTER, HTML_OLD, JS_OLD, MODE_OLD):
        assert html.count(old) == 1, "submit button changed upstream; patch by hand: " + old[:60]
    html = html.replace(CSS_AFTER, CSS_AFTER + CSS)
    html = html.replace(HTML_OLD, HTML_NEW)
    html = html.replace(JS_OLD, JS_NEW)
    html = html.replace(MODE_OLD, MODE_NEW)
    return html


if __name__ == "__main__":
    from pathlib import Path
    p = Path(__file__).resolve().parent.parent / "src" / "embeds" / "events-globe.html"
    p.write_text(apply(p.read_text(encoding="utf-8")), encoding="utf-8")
    print("patched", p)
