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
]

src = Path(sys.argv[1]).read_text(encoding="utf-8")
start = src.index("\n<style>\n") + 1   # the globe's own styles, not the host wrapper's
end = src.rindex("</script>") + len("</script>")
html = src[start:end]

html, n = re.subn(r'<h1 class="esg-title"([^>]*)>(.*?)</h1>', r'<h2 class="esg-title"\1>\2</h2>', html)
assert n == 1, "title not found"

for name in REMOVE_NAMES:
    html = re.sub(r'\n[ \t]*\{"name": "' + re.escape(name) + r'",[^\n]*', "", html)

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

out = Path(__file__).resolve().parent.parent / "src" / "embeds" / "events-globe.html"
out.write_text(html + "\n", encoding="utf-8")
print("wrote", out, len(html), "bytes")
