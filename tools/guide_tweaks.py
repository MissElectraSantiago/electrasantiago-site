"""M's 23 Nov 2026 changes to the Fetish Shopping Guide.

1. The row of city links becomes a dropdown that shows one city at a time.
2. "Map, hours and website" is a highlighted button right under the shop's area line.
3. City names are red.
4. The city list is split into pages of 6 cities, with Previous and Next buttons.
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
        return apply_pages(html)
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
    return apply_pages(html)


# 4. Pages (M, 23 Nov 2026)
PG_CSS_AFTER = '.ess-empty { padding: 40px 0; color: var(--ink-soft); }'
PG_CSS = """
.ess-pager { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 24px 0 4px; }
.ess-pager[hidden] { display: none; }
.ess-pg { min-height: 44px; padding: 0 18px; border: 1px solid var(--ink); border-radius: 999px; background: transparent; color: var(--ink); font: inherit; font-size: 14px; font-weight: 600; cursor: pointer; white-space: nowrap; }
.ess-pg:hover:not(:disabled) { background: var(--ink); color: var(--paper); }
.ess-pg:disabled { opacity: .35; cursor: default; }
.ess-pg-n { font-size: 14px; color: var(--ink-soft); font-variant-numeric: tabular-nums; text-align: center; }"""
PG_HTML_OLD = '    <div id="ess-list"></div>\n'
PG_HTML_NEW = '    <div id="ess-list"></div>\n    <nav class="ess-pager" id="ess-pager" aria-label="Pages" hidden></nav>\n'
PG_STATE_OLD = 'var state = { q: "", city: "", region: "all",'
PG_STATE_NEW = 'var PER_PAGE = 6; // cities per page\n  var state = { q: "", city: "", page: 1, region: "all",'
PG_RENDER_OLD = '  function render() {\n'
PG_RENDER_NEW = '  function render(keepPage) {\n    if (!keepPage) state.page = 1;\n'
PG_EMPTY_OLD = "    if (!vis.length) { $(\"ess-list\").innerHTML"
PG_EMPTY_NEW = "    if (!vis.length) { $(\"ess-pager\").hidden = true; $(\"ess-list\").innerHTML"
PG_SLICE_OLD = '    $("ess-list").innerHTML = vis.map(function (v) {\n'
PG_SLICE_NEW = """    var pages = Math.max(1, Math.ceil(vis.length / PER_PAGE)), pg = $("ess-pager");
    if (state.page > pages) state.page = pages;
    if (pages > 1) {
      pg.innerHTML = '<button type="button" class="ess-pg" data-pg="-1"' + (state.page === 1 ? " disabled" : "") + '>← Previous</button>' +
        '<span class="ess-pg-n">Page ' + state.page + " of " + pages + "</span>" +
        '<button type="button" class="ess-pg" data-pg="1"' + (state.page === pages ? " disabled" : "") + ">Next →</button>";
      pg.hidden = false;
    } else { pg.hidden = true; pg.innerHTML = ""; }
    vis = vis.slice((state.page - 1) * PER_PAGE, state.page * PER_PAGE);
""" + PG_SLICE_OLD
PG_CLICK_OLD = CLICK_NEW
PG_CLICK_NEW = CLICK_NEW + """
  $("ess-pager").addEventListener("click", function (ev) {
    var b = ev.target.closest("button[data-pg]"); if (!b || b.disabled) return;
    state.page += +b.getAttribute("data-pg");
    render(true);
    var top = document.querySelector("#ess .ess-index");
    if (top) top.scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
  });"""


def apply_pages(html):
    if 'id="ess-pager"' in html:
        return html
    pairs = [(PG_CSS_AFTER, PG_CSS_AFTER + PG_CSS), (PG_HTML_OLD, PG_HTML_NEW), (PG_STATE_OLD, PG_STATE_NEW),
             (PG_RENDER_OLD, PG_RENDER_NEW), (PG_EMPTY_OLD, PG_EMPTY_NEW), (PG_SLICE_OLD, PG_SLICE_NEW), (PG_CLICK_OLD, PG_CLICK_NEW)]
    for old, _ in pairs:
        assert html.count(old) == 1, "guide changed upstream; patch pages by hand: " + old[:60]
    for old, new in pairs:
        html = html.replace(old, new)
    return html


if __name__ == "__main__":
    from pathlib import Path
    p = Path(__file__).resolve().parent.parent / "src" / "embeds" / "fetish-shopping-guide.html"
    p.write_text(apply(p.read_text(encoding="utf-8")), encoding="utf-8")
    print("patched", p)
