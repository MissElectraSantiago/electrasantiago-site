"""Turn the main chat's published Events Globe page into src/embeds/events-globe.html.

Usage: python3 tools/patch_globe.py <published-page.html>

Keeps the globe's own style, section and script blocks (drops the host wrapper and
font links), then applies the site's changes:
- the globe's title becomes an h2 (the page has its own h1)
- labels M asked to remove are dropped
- the mouse wheel zooms the globe whenever the pointer is over it
"""
import re, sys
from pathlib import Path

REMOVE_NAMES = ["Latex 42"]          # M, 23 Nov 2026: "remove Latex 42"
LINK_FIXES = [                        # links M corrected, 23 Nov 2026
    ('"name": "CLAW", ', '"https://www.clawinfo.org/"', '"https://clawinfo.org/"'),
    ('"name": "Lesbenfrühlingstreffen (LFT)", ', '"https://lesbenfruehling.de/de/"', '"https://www.lesbenfruehling.de/de/"'),
    # Bar Ajari's Instagram is gone; link its write-up instead
    ('"name": "Bar Ajari", ', '"https://www.instagram.com/bar_ajari/"', '"https://everyqueer.com/the-very-best-queer-lesbian-bars-in-tokyo/"'),
    # Sapphic Riot has no site of its own listed; use Time Out's page on the bar, not the world roundup
    ('"name": "Sapphic Riot", ', '"https://www.timeout.com/pt/rio-de-janeiro/noticias/quais-sao-os-melhores-espacos-queer-do-mundo-de-acordo-com-os-editores-da-time-out-072026"', '"https://www.timeout.com/chiang-mai/bars-and-pubs/sapphic-riot"'),
]

ADD_AFTER = '{"name": "Provocation Club", '   # new pins M asked for, 23 Nov 2026
ADD_ENTRIES = [
    '{"name": "Dykotomy", "category": "Lesbian and queer women", "city": "Melbourne", "country": "Australia", "lat": -37.8, "lng": 144.98, "start": "", "end": "", "usually": "Every few months", "url": "https://www.eventbrite.com/e/dykotomys-d-valley-tickets-1998408413360", "about": "FLINTA dance parties and a FLINTA+ strip club night, often at New Guernica in Collingwood"},',
    '{"name": "Queer Sauna Sounds", "category": "Mixed fetish party and ball", "city": "Melbourne", "country": "Australia", "lat": -37.82, "lng": 144.97, "start": "", "end": "", "usually": "Every few months", "url": "https://www.ravetemple.com/events", "about": "Rave Temple\'s queer party with DJs in a sauna setting"},',
    # M, 23 Nov 2026: all upcoming Umbral Court events
    '{"name": "Squirting 101 (Umbral Court)", "category": "Kink convention and education", "city": "Austin, TX", "country": "USA", "lat": 30.27, "lng": -97.74, "start": "2026-12-17", "end": "2026-12-17", "usually": "", "url": "https://umbralcourtevents.crd.co/#calendar", "about": "Umbral Court class on squirting anatomy and technique with demo tops and bottoms, at The Eastern Court"},',
    '{"name": "Umbral Court Misfit Christmas Cuddle Puddle", "category": "Mixed fetish party and ball", "city": "Austin, TX", "country": "USA", "lat": 30.27, "lng": -97.74, "start": "2026-12-25", "end": "2026-12-25", "usually": "", "url": "https://umbralcourtevents.crd.co/#calendar", "about": "Free Christmas Day potluck and cuddle party with holiday movies, at The Eastern Court"},',
    '{"name": "Umbral Court New Year\'s Party", "category": "Mixed fetish party and ball", "city": "Austin, TX", "country": "USA", "lat": 30.27, "lng": -97.74, "start": "2026-12-31", "end": "2027-01-01", "usually": "", "url": "https://umbralcourtevents.crd.co/#calendar", "about": "Kink-friendly, LGBTQIA+ inclusive New Year\'s Eve play party at The Eastern Court; RSVP for an invite"},',
    '{"name": "Umbral Court Suds and Sins Foam Play Party", "category": "Mixed fetish party and ball", "city": "Austin, TX", "country": "USA", "lat": 30.27, "lng": -97.74, "start": "2027-01-30", "end": "2027-01-31", "usually": "", "url": "https://umbralcourtevents.crd.co/#calendar", "about": "Foam play party with a heated indoor pool and open bar, at The Foam Court; RSVP for an invite"},',
]

src = Path(sys.argv[1]).read_text(encoding="utf-8")
start = src.index("\n<style>\n") + 1   # the globe's own styles, not the host wrapper's
end = src.rindex("</script>") + len("</script>")
html = src[start:end]

html, n = re.subn(r'<h1 class="esg-title"([^>]*)>(.*?)</h1>', r'<h2 class="esg-title"\1>\2</h2>', html)
assert n == 1, "title not found"

for name in REMOVE_NAMES:
    html = re.sub(r'\n[ \t]*\{"name": "' + re.escape(name) + r'",[^\n]*', "", html)

lines = html.split("\n")
for i, line in enumerate(lines):
    if ADD_AFTER in line:
        indent = line[: len(line) - len(line.lstrip())]
        lines[i + 1:i + 1] = [indent + e for e in ADD_ENTRIES]
        break
else:
    sys.exit("ADD_AFTER entry not found")
html = "\n".join(lines)

for name_key, old, new in LINK_FIXES:
    lines = html.split("\n")
    for i, line in enumerate(lines):
        if name_key in line and old in line:
            lines[i] = line.replace(old, new)
    html = "\n".join(lines)

old_wheel = '''    // trackpad pinch (arrives as ctrl + wheel); plain scrolling still scrolls the page
    canvas.addEventListener("wheel", function (ev) {
      if (!ev.ctrlKey) return;
      ev.preventDefault(); pauseSpin(); setZoom(zoom * Math.exp(-ev.deltaY * 0.01));
    }, { passive: false });'''
new_wheel = '''    // Mouse wheel or trackpad pinch over the globe zooms it (M, 23 Nov 2026).
    canvas.addEventListener("wheel", function (ev) {
      var dy = ev.deltaY * (ev.deltaMode === 1 ? 16 : ev.deltaMode === 2 ? 400 : 1);
      ev.preventDefault(); pauseSpin();
      setZoom(zoom * Math.exp(-dy * (ev.ctrlKey ? 0.01 : 0.0015)));
    }, { passive: false });'''
assert old_wheel in html, "wheel handler changed upstream; patch by hand"
html = html.replace(old_wheel, new_wheel)
html = html.replace("<span>Drag to turn · pinch to zoom · tap a pin</span>",
                    "<span>Drag to turn · scroll or pinch to zoom · tap a pin</span>")

# 23 Nov 2026: notes go to Electra through the site's own send-note script
html = html.replace('var SUGGEST_URL = "PASTE_YOUR_SUGGESTIONS_FORM_LINK_HERE";',
                    'var SUGGEST_URL = "https://electrasantiago.com/send-note.php";')

# M, 23 Nov 2026: let people zoom in 20% further
html = html.replace('function setZoom(z) { zoom = Math.max(1, Math.min(3.2, z)); }',
                    'function setZoom(z) { zoom = Math.max(1, Math.min(3.84, z)); }')
# M, 23 Nov: Charmskool is women owned and operated
html = html.replace('''"tags": ["Latex", "Couture", "Lingerie", "Accessories"], "url": "https://charmskoolshop.com/", "about": "East London showroom and online shop selling handmade latex from independent makers worldwide."}''',
                    '''"tags": ["Women owned", "Latex", "Couture", "Lingerie", "Accessories"], "url": "https://charmskoolshop.com/", "about": "East London showroom and online shop selling handmade latex from independent makers worldwide.", "women": true}''')
# M, 23 Nov: zoom in much closer so the clustered European pins can be tapped one by one on a phone
for a, b in [('function setZoom(z) { zoom = Math.max(1, Math.min(4, z)); }',
              'function setZoom(z) { zoom = Math.max(1, Math.min(16, z)); }'),
             ('setZoom(zoom * 1.35); pauseSpin();', 'setZoom(zoom * 1.6); pauseSpin();'),
             ('setZoom(zoom / 1.35);', 'setZoom(zoom / 1.6);'),
             # once zoomed in, the globe stays put instead of spinning away
             ('idleTimer = setTimeout(function () { if (!state.place && !hover) spinning = true; }, 9000);',
              'idleTimer = setTimeout(function () { if (!state.place && !hover && zoom < 1.5) spinning = true; }, 9000);'),
             ('rot[0] += (time - t0) * 0.006;', 'rot[0] += (time - t0) * 0.006 / zoom;')]:
    if a in html:
        html = html.replace(a, b)

# M, 23 Nov 2026: make the events / fashion switch easier to spot
SWITCH = [('.esg-mode { display: inline-flex; border: 1px solid var(--ink); border-radius: 999px; overflow: hidden; }\n.esg-mode button { height: 44px; padding: 0 22px; border: 0; background: transparent; color: var(--ink); font-family: var(--display); font-size: 14px; letter-spacing: 0.08em; text-transform: uppercase; cursor: pointer; }\n.esg-mode button + button { border-left: 1px solid var(--ink); }\n.esg-mode button[aria-pressed="true"] { background: var(--ink); color: var(--paper); }', '.esg-switch { display: grid; gap: 8px; justify-items: start; }\n.esg-switch-label { margin: 0; font-size: 13px; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: var(--red); }\n.esg-mode { display: inline-flex; border: 2px solid var(--red); border-radius: 999px; overflow: hidden; box-shadow: 0 0 0 4px color-mix(in srgb, var(--red) 18%, transparent); }\n.esg-mode button { height: 52px; padding: 0 30px; border: 0; background: transparent; color: var(--ink); font-family: var(--display); font-size: 16px; letter-spacing: 0.08em; text-transform: uppercase; cursor: pointer; transition: background .15s ease; }\n.esg-mode button + button { border-left: 2px solid var(--red); }\n.esg-mode button:hover { background: color-mix(in srgb, var(--red) 14%, transparent); }\n.esg-mode button[aria-pressed="true"] { background: var(--red); color: var(--red-ink); }\n@media (max-width: 560px) { .esg-switch, .esg-mode { width: 100%; } .esg-mode button { flex: 1; padding: 0 12px; } }'), ('      <div class="esg-mode" role="group" aria-label="Show events or fashion">\n        <button type="button" data-mode="events" aria-pressed="true">Events</button>\n        <button type="button" data-mode="fashion" aria-pressed="false">Fashion</button>\n      </div>', '      <div class="esg-switch">\n        <p class="esg-switch-label" id="esg-switch-label">Switch the map</p>\n        <div class="esg-mode" role="group" aria-labelledby="esg-switch-label">\n          <button type="button" data-mode="events" aria-pressed="true">Events</button>\n          <button type="button" data-mode="fashion" aria-pressed="false">Fashion</button>\n        </div>\n      </div>')]
for old, new in SWITCH:
    assert old in html, 'switch changed upstream; patch by hand'
    html = html.replace(old, new)

# 23 Nov 2026: the Submit button opens a form that sends through send-note.php
sys.path.insert(0, str(Path(__file__).resolve().parent))
import globe_submit_form
html = globe_submit_form.apply(html)

out = Path(__file__).resolve().parent.parent / "src" / "embeds" / "events-globe.html"
out.write_text(html + "\n", encoding="utf-8")
print("wrote", out, len(html), "bytes")
