"""M's 23 Nov 2026 changes to the Fetish Shopping Guide.

1. The row of city links becomes a dropdown that shows one city at a time.
2. "Map, hours and website" is a highlighted button right under the shop's area line.
3. City names are red.
Used by tools/embed_page.py, and can be run on its own.
"""

CSS_OLD = '.ess-cities { display: flex;'
CSS_ADD = '''.ess-pick { position: relative; display: block; max-width: 420px; }
.ess-pick select { width: 100%; height: 48px; padding: 0 44px 0 18px; border: 1px solid var(--ink); border-radius: 999px; background: var(--paper); color: var(--ink); font-family: var(--display); font-size: 15px; letter-spacing: 0.04em; text-transform: uppercase; appearance: none; -webkit-appearance: none; cursor: pointer; }
.ess-pick::after { content: ""; position: absolute; right: 20px; top: 50%; width: 8px; height: 8px; border-right: 2px solid var(--ink); border-bottom: 2px solid var(--ink); transform: translateY(-70%) rotate(45deg); pointer-events: none; }
.ess-pick select:focus-visible { outline: 2px solid var(--red); outline-offset: 2px; }
'''
NAME_OLD = '.ess-city-name { margin: 0;'
NAME_NEW = '.ess-city-name { color: var(--red); margin: 0;'
MAP_OLD = '.ess-map { margin-top: auto; padding-top: 6px; align-self: flex-start; font-size: 14px; font-weight: 500; color: var(--ink); text-decoration: underline; text-underline-offset: 3px; text-decoration-color: var(--line); }\n.ess-map:hover { text-decoration-color: var(--ink); }'
MAP_NEW = '.ess-map { align-self: flex-start; display: inline-flex; align-items: center; min-height: 40px; margin: 4px 0 2px; padding: 0 18px; border-radius: 999px; background: var(--red); color: var(--red-ink); font-size: 14px; font-weight: 600; text-decoration: none; }\n.ess-map:hover { filter: brightness(0.92); }\n.ess-map:focus-visible { outline: 2px solid var(--ink); outline-offset: 2px; }'

HTML_OLD = '      <ul class="ess-cities" id="ess-cities"></ul>'
HTML_NEW = '      <label class="ess-pick" for="ess-city-pick"><span class="ess-sr">City</span><select id="ess-city-pick" aria-label="Choose a city"></select></label>'
SR_CSS = '.ess-sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }\n'

CLICK_OLD = '''  $("ess-cities").addEventListener("click", function (ev) {
    var a = ev.target.closest("a"); if (!a) return;
    ev.preventDefault();
    var el = document.getElementById(a.getAttribute("data-to"));
    if (el) el.scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
  });'''
CLICK_NEW = '''  $("ess-city-pick").addEventListener("change", function () { state.city = this.value; render(); });'''

RESET_OLD = 'state.q = ""; qEl.value = ""; qClear.hidden = true; state.sells.clear(); state.region = "all";'
RESET_NEW = 'state.q = ""; qEl.value = ""; qClear.hidden = true; state.sells.clear(); state.region = "all"; state.city = "";'

RENDER_OLD = '''    $("ess-cities").innerHTML = vis.map(function (v) {
      var soon = v.h.events.some(function (e) { return e.live || (e.s && e.days <= 30); });
      return '<li><a href="#' + v.h.id + '" data-to="' + v.h.id + '">' + esc(v.h.name) + (soon ? '<span class="ess-mark" aria-label="event in the next 30 days"></span>' : "") + "</a></li>";
    }).join("");'''
RENDER_NEW = '''    if (state.city && !vis.some(function (v) { return v.h.id === state.city; })) state.city = "";
    $("ess-city-pick").innerHTML = '<option value="">All cities (' + vis.length + ')</option>' + vis.map(function (v) {
      var soon = v.h.events.some(function (e) { return e.live || (e.s && e.days <= 30); });
      return '<option value="' + v.h.id + '"' + (v.h.id === state.city ? " selected" : "") + ">" + esc(v.h.name) + (soon ? " · event soon" : "") + "</option>";
    }).join("");
    if (state.city) vis = vis.filter(function (v) { return v.h.id === state.city; });'''

VIS_OLD = '    var vis = visible(), nShops = 0, nCities = 0;'
STATE_OLD = 'var state = { q: "", region: "all",'
STATE_NEW = 'var state = { q: "", city: "", region: "all",'
FILT_OLD = 'var filtered = state.q || state.sells.size || state.region !== "all";'
FILT_NEW = 'var filtered = state.q || state.city || state.sells.size || state.region !== "all";'

SHOP_OLD_AREA = '''      (s.area ? '<p class="ess-shop-area">' + esc(s.area) + "</p>" : "") +'''
SHOP_MAP = '''      '<a class="ess-map" href="' + esc(mapUrl(s, h)) + '" target="_blank" rel="noopener">Map, hours and website ↗</a>' +\n'''


def apply(html):
    if 'id="ess-city-pick"' in html:
        return html
    for old in (CSS_OLD, NAME_OLD, MAP_OLD, HTML_OLD, CLICK_OLD, RESET_OLD, RENDER_OLD, VIS_OLD, STATE_OLD, FILT_OLD, SHOP_OLD_AREA, SHOP_MAP):
        assert html.count(old) == 1, "guide changed upstream; patch by hand: " + old[:60]
    html = html.replace(CSS_OLD, SR_CSS + CSS_ADD + CSS_OLD)
    html = html.replace(NAME_OLD, NAME_NEW)
    html = html.replace(MAP_OLD, MAP_NEW)
    html = html.replace(HTML_OLD, HTML_NEW)
    html = html.replace(CLICK_OLD, CLICK_NEW)
    html = html.replace(RESET_OLD, RESET_NEW)
    html = html.replace(RENDER_OLD, "")
    html = html.replace(VIS_OLD, VIS_OLD + "\n" + RENDER_NEW)
    html = html.replace(STATE_OLD, STATE_NEW)
    html = html.replace(FILT_OLD, FILT_NEW)
    html = html.replace(SHOP_MAP, "")
    html = html.replace(SHOP_OLD_AREA, SHOP_OLD_AREA + "\n" + SHOP_MAP.rstrip("\n"))
    return html


if __name__ == "__main__":
    from pathlib import Path
    p = Path(__file__).resolve().parent.parent / "src" / "embeds" / "fetish-shopping-guide.html"
    p.write_text(apply(p.read_text(encoding="utf-8")), encoding="utf-8")
    print("patched", p)
