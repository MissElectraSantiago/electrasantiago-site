"""On phones, tapping a pin shows a small preview card right under the globe
instead of scrolling the page down to the list (M, 23 Nov 2026). The card has
the city, up to three listings, a close button and a link down to the full list.
It sits under the globe, so it never covers other pins. Used by tools/patch_globe.py.
"""

CSS_AFTER = '.esg-tip.esg-on { opacity: 1; }'
CSS = '''
.esg-peek { display: none; }
@media (max-width: 860px) {
  .esg-peek:not([hidden]) { display: block; max-width: 420px; margin: 12px auto 0; padding: 12px 14px 14px; border: 1px solid var(--ink); border-radius: 18px; background: var(--paper); font-size: 14px; }
}
.esg-peek-head { display: flex; align-items: center; gap: 4px 10px; flex-wrap: wrap; }
.esg-peek-head b { font-family: var(--display); font-weight: 400; font-size: 18px; line-height: 1.1; }
.esg-peek-head span { color: var(--ink-soft); font-size: 13px; }
.esg-peek-x { margin-left: auto; width: 34px; height: 34px; border-radius: 50%; border: 1px solid var(--line); background: transparent; color: var(--ink); font-size: 18px; line-height: 1; cursor: pointer; }
.esg-peek ul { list-style: none; margin: 8px 0 12px; padding: 0; display: grid; gap: 8px; }
.esg-peek li { display: flex; flex-wrap: wrap; align-items: baseline; gap: 2px 10px; }
.esg-peek-name { font-weight: 600; min-width: 0; }
.esg-peek-when { color: var(--ink-soft); font-size: 13px; }
.esg-peek li a { margin-left: auto; color: var(--red); font-size: 13px; white-space: nowrap; }
.esg-peek-more { width: 100%; height: 42px; border: 0; border-radius: 999px; background: var(--red); color: var(--red-ink); font: inherit; font-weight: 600; cursor: pointer; }'''

HTML_OLD = '''        <div class="esg-legend">'''
HTML_NEW = '''        <div class="esg-peek" id="esg-peek" aria-live="polite" hidden></div>
        <div class="esg-legend">'''

RENDER_OLD = '''    var px = $("esg-place-x"); if (px) px.addEventListener("click", function () { state.place = null; render(); });
'''
RENDER_NEW = RENDER_OLD + '''
    var pk = $("esg-peek");
    if (state.place && shown.length) {
      var items = mode === "fashion" ? shown : dated.concat(venues, tba);
      var ph = '<div class="esg-peek-head"><b>' + esc(state.place) + "</b><span>" + st + '</span><button type="button" class="esg-peek-x" aria-label="Close preview">×</button></div><ul>';
      items.slice(0, 3).forEach(function (o) {
        var w = mode === "fashion" ? (o.women ? "Women owned" : o.online ? "Online only" : "") : o.venue ? "Open year-round" : o.s ? dateRange(o) : "Dates TBA";
        ph += '<li><span class="esg-peek-name">' + esc(o.name) + "</span>" + (w ? '<span class="esg-peek-when">' + w + "</span>" : "") +
          (o.url ? '<a href="' + esc(o.url) + '" target="_blank" rel="noopener nofollow">' + (mode === "fashion" ? "Shop" : "Website") + "</a>" : "") + "</li>";
      });
      ph += '</ul><button type="button" class="esg-peek-more">' + (items.length > 3 ? "See all " + items.length + " in the list" : "See the details below") + "</button>";
      pk.innerHTML = ph; pk.hidden = false;
      pk.querySelector(".esg-peek-x").addEventListener("click", function () { state.place = null; render(); });
      pk.querySelector(".esg-peek-more").addEventListener("click", function () { $("esg-status").scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "start" }); });
    } else { pk.hidden = true; pk.innerHTML = ""; }
'''

SCROLL_OLD = '''      if (window.matchMedia("(max-width: 860px)").matches && state.place) $("esg-status").scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "start" });
'''


def apply(html):
    if 'id="esg-peek"' in html:
        return html
    for old in (CSS_AFTER, HTML_OLD, RENDER_OLD, SCROLL_OLD):
        assert html.count(old) == 1, "globe changed upstream; patch the phone preview by hand: " + old[:60]
    html = html.replace(CSS_AFTER, CSS_AFTER + CSS)
    html = html.replace(HTML_OLD, HTML_NEW)
    html = html.replace(RENDER_OLD, RENDER_NEW)
    html = html.replace(SCROLL_OLD, "")
    return html


if __name__ == "__main__":
    from pathlib import Path
    p = Path(__file__).resolve().parent.parent / "src" / "embeds" / "events-globe.html"
    p.write_text(apply(p.read_text(encoding="utf-8")), encoding="utf-8")
    print("patched", p)
