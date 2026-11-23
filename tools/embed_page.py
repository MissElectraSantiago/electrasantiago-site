"""Turn a page published in the main chat into an embed for the site.

Usage: python3 tools/embed_page.py <published-page.html> <embed-name>

Keeps the page's own style, section and script blocks (drops the host wrapper and
font links) and fills in settings that point at this site. The site page that uses
the embed (src/pages/<name>.html) sets the dark colours.
"""
import sys
from pathlib import Path

SETTINGS = {
    "holiday-giving-guide": [
        ('var PAGE_URL = "https://electrasantiago.com/";', 'var PAGE_URL = "https://electrasantiago.com/holiday-giving-guide";'),
    ],
    "getting-started-in-kink": [
        ('"name": "Black Rose", "url": "https://br.org/br/about-black-rose/"', '"name": "Black Rose", "url": "https://br.org/"'),  # M, 23 Nov 2026
        ('"url": "https://clawinfo.org/claw-26-registration-information"', '"url": "https://clawinfo.org/"'),  # M, 23 Nov 2026
    ],
    "fetish-shopping-guide": [
        ('var EVENTS_PAGE_URL = "";', 'var EVENTS_PAGE_URL = "https://electrasantiago.com/community-resources";'),
    ],
}

src = Path(sys.argv[1]).read_text(encoding="utf-8")
name = sys.argv[2]
html = src[src.index("\n<style>\n") + 1: src.rindex("</script>") + len("</script>")]
for old, new in SETTINGS.get(name, []):
    assert old in html, f"setting not found: {old}"
    html = html.replace(old, new)
out = Path(__file__).resolve().parent.parent / "src" / "embeds" / f"{name}.html"
out.write_text(html + "\n", encoding="utf-8")
print("wrote", out, len(html), "bytes")
