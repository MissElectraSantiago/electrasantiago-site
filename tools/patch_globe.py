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

out = Path(__file__).resolve().parent.parent / "src" / "embeds" / "events-globe.html"
out.write_text(html + "\n", encoding="utf-8")
print("wrote", out, len(html), "bytes")
