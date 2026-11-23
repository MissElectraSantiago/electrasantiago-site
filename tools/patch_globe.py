"""Turn the main chat's published Events Globe page into src/embeds/events-globe.html.

Usage: python3 tools/patch_globe.py <published-page.html>

Keeps the globe's own style, section and script blocks (drops the host wrapper and
font links), then applies the site's changes:
- the globe's title becomes an h2 (the page has its own h1)
- labels M asked to remove are dropped
- the mouse wheel zooms the globe once she has grabbed or clicked it
"""
import re, sys
from pathlib import Path

REMOVE_NAMES = ["Latex 42"]          # M, 23 Nov 2026: "remove Latex 42"

src = Path(sys.argv[1]).read_text(encoding="utf-8")
start = src.index("\n<style>\n") + 1   # the globe's own styles, not the host wrapper's
end = src.rindex("</script>") + len("</script>")
html = src[start:end]

html, n = re.subn(r'<h1 class="esg-title"([^>]*)>(.*?)</h1>', r'<h2 class="esg-title"\1>\2</h2>', html)
assert n == 1, "title not found"

for name in REMOVE_NAMES:
    html = re.sub(r'\n[ \t]*\{"name": "' + re.escape(name) + r'",[^\n]*', "", html)

old_wheel = '''    // trackpad pinch (arrives as ctrl + wheel); plain scrolling still scrolls the page
    canvas.addEventListener("wheel", function (ev) {
      if (!ev.ctrlKey) return;
      ev.preventDefault(); pauseSpin(); setZoom(zoom * Math.exp(-ev.deltaY * 0.01));
    }, { passive: false });'''
new_wheel = '''    // Plain mouse wheel zooms once the globe has been grabbed or clicked, until the pointer
    // moves off it; at full zoom in or out the wheel scrolls the page as usual.
    var engagedUntil = 0;
    function engage() { engagedUntil = Infinity; }
    canvas.addEventListener("pointerdown", engage);
    canvas.addEventListener("pointerup", engage);
    canvas.addEventListener("pointerleave", function () { if (!drag) engagedUntil = 0; });
    canvas.addEventListener("wheel", function (ev) {
      var dy = ev.deltaY * (ev.deltaMode === 1 ? 16 : ev.deltaMode === 2 ? 400 : 1);
      if (ev.ctrlKey) { ev.preventDefault(); pauseSpin(); setZoom(zoom * Math.exp(-dy * 0.01)); return; }
      if (!drag && performance.now() > engagedUntil) return;
      if ((dy > 0 && zoom <= 1) || (dy < 0 && zoom >= 3.2)) return;
      ev.preventDefault(); pauseSpin(); engage(); setZoom(zoom * Math.exp(-dy * 0.0015));
    }, { passive: false });'''
assert old_wheel in html, "wheel handler changed upstream; patch by hand"
html = html.replace(old_wheel, new_wheel)
html = html.replace("<span>Drag to turn · pinch to zoom · tap a pin</span>",
                    "<span>Drag to turn · scroll or pinch to zoom · tap a pin</span>")

out = Path(__file__).resolve().parent.parent / "src" / "embeds" / "events-globe.html"
out.write_text(html + "\n", encoding="utf-8")
print("wrote", out, len(html), "bytes")
