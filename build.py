#!/usr/bin/env python3
"""Build electrasantiago.com from src/ into public/ (the live site).

Usage:
  python3 build.py            -> public/   (upload this folder to the host)
  python3 build.py --preview  -> preview/  (self-contained preview: .html links,
                                            inlined CSS/JS, no iframes, drafts shown)

Pages live in src/pages/*.html, each starting with a <!--meta {json} --> block.
Blog posts live in src/posts/*.md (one file per post, see src/posts/README.md).
Photos go in src/images/<name>.jpg (or .webp/.png); a missing photo shows a placeholder.
Needs: pip install markdown
"""
import datetime as dt
import hashlib
import html
import json
import re
import shutil
import sys
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
PREVIEW = "--preview" in sys.argv
OUT = ROOT / ("preview" if PREVIEW else "public")
SITE = json.loads((SRC / "site.json").read_text(encoding="utf-8"))
BASE = SITE["base_url"].rstrip("/")
TODAY = dt.date.today().isoformat()

FONTS = ("https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;"
         "0,9..40,700;1,9..40,400&family=Oswald:wght@400;500;600;700&display=swap")
FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E"
           "%3Crect width='64' height='64' fill='%230b0a0d'/%3E%3Ctext x='32' y='44' font-family='Impact,sans-serif' "
           "font-size='34' fill='%23e3141c' text-anchor='middle'%3EES%3C/text%3E%3C/svg%3E")
RTA = "RTA-5042-1996-1400-1577-RTA"


def esc(s):
    return html.escape(str(s), quote=True)


# ---------- content loading ----------

def load_pages():
    pages = []
    for f in sorted((SRC / "pages").glob("*.html")):
        text = f.read_text(encoding="utf-8")
        m = re.match(r"\s*<!--meta\s*(\{.*?\})\s*-->\s*", text, re.S)
        if not m:
            raise SystemExit(f"{f.name}: missing <!--meta {{...}} --> block")
        meta = json.loads(m.group(1))
        meta["body"] = text[m.end():]
        meta["file"] = f.stem
        pages.append(meta)
    return pages


def parse_front_matter(text, name):
    m = re.match(r"---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        raise SystemExit(f"{name}: missing --- front matter ---")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            v = v.strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                v = v[1:-1]
            meta[k.strip()] = v
    return meta, text[m.end():]


def load_posts():
    posts = []
    folder = SRC / "posts"
    for f in sorted(folder.glob("*.md")):
        if f.name.lower() == "readme.md":
            continue
        meta, body = parse_front_matter(f.read_text(encoding="utf-8"), f.name)
        meta["slug"] = meta.get("slug") or f.stem
        meta["draft"] = meta.get("draft", "false").lower() == "true"
        if meta["draft"] and not PREVIEW:
            continue
        for key in ("title", "date", "description"):
            if not meta.get(key):
                raise SystemExit(f"{f.name}: front matter needs '{key}'")
        body = re.sub(r"^\[image: ?(.*?)\]\s*$", lambda mm: "{{pimg:" + meta["slug"] + "|" + mm.group(1) + "}}",
                      body, flags=re.M)
        if not meta.get("image") and (SRC / "images" / f'{meta["slug"]}.jpg').exists():
            meta["image"] = f'/images/{meta["slug"]}.jpg'
        meta["html"] = markdown.markdown(body, extensions=["extra", "sane_lists"])
        words = len(re.sub(r"<[^>]+>", " ", meta["html"]).split())
        meta["minutes"] = max(1, round(words / 220))
        posts.append(meta)
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


# ---------- small renderers ----------

def seo_desc(text, limit=158):
    """Search engines show about 155 characters; cut long descriptions at a word."""
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(",;:.")
    return cut + "…"


def nice_date(iso):
    d = dt.date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%B %Y')}"


def find_image(name):
    for ext in ("webp", "jpg", "jpeg", "png"):
        f = SRC / "images" / f"{name}.{ext}"
        if f.exists():
            if PREVIEW:
                return f"images/{name}.{ext}"
            # a version tag from the file's contents, so a replaced photo is never served from an old cache
            return f"/images/{name}.{ext}?v={hashlib.sha1(f.read_bytes()).hexdigest()[:8]}"
    return None


def image(name, alt, lazy=True):
    src = find_image(name)
    if src:
        load = ' loading="lazy"' if lazy else ' fetchpriority="high"'
        return f'<img src="{src}" alt="{esc(alt)}"{load} decoding="async">'
    return f'<div class="ph" role="img" aria-label="{esc(alt)}">Photo: {esc(name)}</div>'


def jotform(key, label):
    form_id = SITE["forms"][key]
    url = f"https://form.jotform.com/{form_id}"
    link = (f'<div class="embed-link"><h3>{esc(label)}</h3>'
            f'<p class="muted">The form opens in a new tab. It takes about five minutes.</p>'
            f'<a class="btn btn-red" href="{url}" target="_blank" rel="noopener">Open the form</a></div>')
    if PREVIEW:
        return f'<div class="embed">{link}</div>'
    return (f'<div class="embed"><iframe src="{url}" title="{esc(label)}" loading="lazy" '
            f'allow="fullscreen"></iframe><noscript>{link}</noscript></div>'
            f'<p class="small muted" style="margin-top:.75rem;">Form not loading? <a href="{url}" target="_blank" rel="noopener">Open it in a new tab</a>.</p>')


def post_card(p):
    draft = ' <span class="meta" style="color:var(--red)">· Draft</span>' if p["draft"] else ""
    return (f'<article class="card"><p class="meta"><time datetime="{p["date"]}">{nice_date(p["date"])}</time>'
            f' · {p["minutes"]} min read{draft}</p>'
            f'<h3><a href="/{p["slug"]}">{esc(p["title"])}</a></h3>'
            f'<p class="muted">{esc(seo_desc(p["description"], 200))}</p></article>')


def hero_image(name, alt):
    """Hero photo; a <name>-mobile crop, if present, is used on phones so the face clears the title."""
    img = image(name, alt, lazy=False)
    mobile = find_image(f"{name}-mobile")
    if not mobile:
        return img
    return f'<picture><source media="(max-width: 760px)" srcset="{mobile}">{img}</picture>'


BLANK = "data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=="


def hero_show(prefix, alt):
    """Opening slideshow: <prefix>01, <prefix>02 ... each with an optional -mobile crop.
    A slide with no phone crop is shown on wide screens only. Only the first loads up front."""
    slides, n = [], 1
    while find_image(f"{prefix}{n:02d}"):
        slides.append(f"{prefix}{n:02d}"); n += 1
    if not slides:
        return f'<div class="neon" role="img" aria-label="{esc(alt)}"></div>'
    out = []
    for i, name in enumerate(slides):
        desk, mob = find_image(name), find_image(f"{name}-mobile")
        if i == 0:
            src = f'<source media="(max-width: 760px)" srcset="{mob}">' if mob else ""
            out.append(f'<picture class="slide is-on">{src}<img src="{desk}" alt="{esc(alt)}" fetchpriority="high" decoding="async"></picture>')
        else:
            src = f'<source media="(max-width: 760px)" data-srcset="{mob}">' if mob else ""
            cls = "slide" if mob else "slide desk-only"
            out.append(f'<picture class="{cls}">{src}<img src="{BLANK}" data-src="{desk}" alt="" decoding="async"></picture>')
    return f'<div class="slides" data-slides>{"".join(out)}</div>'


def expand(body, posts):
    body = re.sub(r"\{\{heroshow:([\w-]+)\|(.*?)\}\}", lambda m: hero_show(m.group(1), m.group(2)), body)
    body = re.sub(r"\{\{hero:([\w-]+)\|(.*?)\}\}",
                  lambda m: hero_image(m.group(1), m.group(2)) if find_image(m.group(1))
                  else f'<div class="neon" role="img" aria-label="{esc(m.group(2))}"></div>', body)
    body = re.sub(r"<p>\{\{pimg:([\w-]+)\|(.*?)\}\}</p>",
                  lambda m: (f'<figure class="frame post-photo">{image(m.group(1), m.group(2))}</figure>'
                             if find_image(m.group(1)) else ""), body)
    body = re.sub(r"\{\{embed:([\w-]+)\}\}", lambda m: (SRC / "embeds" / f"{m.group(1)}.html").read_text(encoding="utf-8"), body)
    body = re.sub(r"\{\{img:([\w-]+)\|(.*?)\}\}", lambda m: image(m.group(1), m.group(2)), body)
    body = re.sub(r"\{\{jotform:(\w+)\|(.*?)\}\}", lambda m: jotform(m.group(1), m.group(2)), body)
    body = re.sub(r"\{\{latest_posts:(\d+)\}\}",
                  lambda m: '<div class="cards">' + "".join(post_card(p) for p in posts[:int(m.group(1))]) + "</div>",
                  body)
    body = body.replace("{{post_list}}", '<div class="cards">' + "".join(post_card(p) for p in posts) + "</div>")
    body = body.replace("{{telegram_dm}}", SITE["telegram_dm"]).replace("{{telegram}}", SITE["telegram"]).replace("{{email}}", esc(SITE["email"]))
    body = body.replace("{{mentorship_endpoint}}", esc(SITE["forms"]["mentorship_endpoint"]))
    return body


# ---------- structured data ----------

def person():
    return {"@type": "Person", "@id": f"{BASE}/#person", "name": "Electra Santiago",
            "alternateName": "Miss Electra Santiago", "url": f"{BASE}/",
            "jobTitle": "Online Dominatrix and femdom content creator",
            "description": "Miss Electra Santiago is an online Dominatrix and femdom content creator offering video calls, custom videos and mentorship for adult content creators.",
            "image": BASE + SITE["og_image"],
            "homeLocation": {"@type": "Place", "name": "Melbourne, Australia"},
            "sameAs": SITE["same_as"]}


SERVICES = {
    "session": ("Online fetish domination video session", "/online-fetish-domination",
                [("10 minutes", "200"), ("20 minutes", "300"), ("30 minutes", "400"), ("One hour", "600")]),
    "custom": ("Custom femdom video", "/online-fetish-domination#custom", []),
    "mentorship": ("Mentorship for adult content creators", "/mentorship-for-creators",
                   [("One-time 60-minute call", "149"), ("3-call strategy package", "399")]),
}


def schema_for(meta, posts, post=None):
    graph = []
    url = BASE + (meta["path"] if meta["path"] != "/" else "/")
    for kind in meta.get("schema", []):
        if kind == "person":
            graph.append(person())
        elif kind == "website":
            graph.append({"@type": "WebSite", "@id": f"{BASE}/#website", "url": f"{BASE}/",
                          "name": "Electra Santiago", "publisher": {"@id": f"{BASE}/#person"}, "inLanguage": "en"})
        elif kind.startswith("service:"):
            name, path, offers = SERVICES[kind.split(":", 1)[1]]
            s = {"@type": "Service", "name": name, "url": BASE + path, "areaServed": "Worldwide (online)",
                 "provider": {"@type": "Person", "@id": f"{BASE}/#person", "name": "Electra Santiago", "url": f"{BASE}/"}}
            if offers:
                s["offers"] = [{"@type": "Offer", "name": n, "price": p, "priceCurrency": "USD"} for n, p in offers]
            graph.append(s)
        elif kind == "blog":
            graph.append({"@type": "Blog", "name": "The Femdom Authority Blog", "url": url,
                          "author": {"@type": "Person", "@id": f"{BASE}/#person", "name": "Electra Santiago", "url": f"{BASE}/"},
                          "blogPost": [{"@type": "BlogPosting", "headline": p["title"], "url": f"{BASE}/{p['slug']}",
                                        "datePublished": p["date"]} for p in posts]})
        elif kind == "breadcrumb":
            items = [{"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE}/"}]
            if post:
                items.append({"@type": "ListItem", "position": 2, "name": "Blog", "item": f"{BASE}/blog-list"})
            items.append({"@type": "ListItem", "position": len(items) + 1, "name": meta.get("crumb", meta["title"]),
                          "item": url})
            graph.append({"@type": "BreadcrumbList", "itemListElement": items})
        elif kind == "post" and post:
            bp = {"@type": "BlogPosting", "headline": post["title"], "description": post["description"],
                  "datePublished": post["date"], "dateModified": post.get("updated") or post["date"],
                  "mainEntityOfPage": url, "url": url, "inLanguage": "en",
                  "author": {"@type": "Person", "@id": f"{BASE}/#person", "name": "Electra Santiago", "url": f"{BASE}/"},
                  "publisher": {"@type": "Person", "@id": f"{BASE}/#person", "name": "Electra Santiago", "url": f"{BASE}/"},
                  "image": BASE + (post.get("image") or SITE["og_image"])}
            graph.append(bp)
    if not graph:
        return ""
    data = {"@context": "https://schema.org", "@graph": graph}
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + "</script>"


# ---------- layout ----------

def header(current):
    links = "".join(
        f'<a href="{href}"{" aria-current=\"page\"" if href == current else ""}>{esc(label)}</a>'
        for label, href in SITE["nav"])
    return f'''<a class="skip" href="#main">Skip to content</a>
<header class="site-header">
  <div class="wrap">
    <a class="logo" href="/" aria-label="Electra Santiago, home"><span>Electra</span><span>Santiago</span></a>
    <button class="menu-btn" type="button" aria-controls="site-nav" aria-expanded="false">Menu</button>
    <nav class="nav" id="site-nav" aria-label="Main">{links}<a class="nav-cta" href="{SITE["onlyfans_cta"]}" rel="noopener">OnlyFans</a></nav>
  </div>
</header>'''


def footer():
    cols = ""
    for title, links in SITE["footer"]:
        items = "".join(f'<li><a href="{esc(u)}" rel="noopener">{esc(n)}</a></li>' for n, u in links)
        cols += f'<div><h2>{esc(title)}</h2><ul>{items}</ul></div>'
    endpoint = esc(SITE["forms"]["mailing_list_endpoint"])
    year = dt.date.today().year
    return f'''<footer class="site-footer">
  <div class="wrap">
    <div class="foot-grid">
      <div>
        <h2>Join my mailing list</h2>
        <form class="stack" data-form data-endpoint="{endpoint}" data-success="You're on the list.">
          <div class="signup">
            <label class="skip" for="ml-email">Email address</label>
            <input id="ml-email" name="email" type="email" required autocomplete="email" placeholder="Your email address">
            <button class="btn btn-red" type="submit">Join</button>
          </div>
          <p class="form-status small" role="status"></p>
        </form>
      </div>
      {cols}
    </div>
    <div class="legal">
      <p>© {year} Electra Santiago. All performers are 18 or older. Adults only.</p>
      <p class="foot-links"><a href="/press">Press</a> · <a href="/gallery">Gallery</a> · <a href="/creator-resources">Creator resources</a> · <a href="/mentorship-for-creators">Mentorship</a></p>
    </div>
  </div>
</footer>'''


def action_bar():
    return (f'<div class="action-bar" aria-label="Quick links">'
            f'<a class="btn btn-red" href="{SITE["onlyfans_cta"]}" rel="noopener">Subscribe on OnlyFans</a>'
            f'<a class="btn btn-ghost" href="{SITE["telegram"]}" rel="noopener">Telegram</a></div>')


def age_gate():
    return '''<div class="gate" id="age-gate" hidden role="dialog" aria-modal="true" aria-labelledby="gate-title">
  <div class="gate-box">
    <p class="age">18+</p>
    <h2 id="gate-title" style="font-size:1.6rem;">Adults only</h2>
    <p class="muted">This site contains adult themes and links to explicit content. By entering you confirm that you are at least 18 years old, or the age of majority where you live, and that viewing it is legal for you.</p>
    <div class="btn-row">
      <button class="btn btn-red" type="button" id="age-enter">I’m 18 or older, enter</button>
      <a class="btn btn-ghost" href="https://www.google.com/">Leave</a>
    </div>
  </div>
</div>'''


def head_tags(meta, posts, post=None, og_type="website"):
    path = meta["path"]
    canonical = BASE + (path if path != "/" else "/")
    img = BASE + ((post or {}).get("image") or SITE["og_image"])
    extra = ""
    if post:
        extra = (f'<meta property="article:published_time" content="{post["date"]}">'
                 f'<meta property="article:author" content="Electra Santiago">')
    return f'''<title>{esc(meta["title"])}</title>
<meta name="description" content="{esc(meta["description"])}">
<link rel="canonical" href="{canonical}">
<meta name="robots" content="index, follow, max-image-preview:large">
<meta name="rating" content="adult">
<meta name="RATING" content="{RTA}">
<meta name="theme-color" content="#0b0a0d">
<meta property="og:site_name" content="Electra Santiago">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{esc(meta["title"])}">
<meta property="og:description" content="{esc(meta["description"])}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{img}">
<meta property="og:locale" content="{SITE["locale"]}">{extra}
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="{SITE["twitter"]}">
<meta name="twitter:title" content="{esc(meta["title"])}">
<meta name="twitter:description" content="{esc(meta["description"])}">
<meta name="twitter:image" content="{img}">
<link rel="icon" href="{FAVICON}">
<link rel="alternate" type="application/rss+xml" title="Electra Santiago blog" href="{BASE}/feed.xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
{schema_for(meta, posts, post)}'''


CSS = (SRC / "assets" / "style.css").read_text(encoding="utf-8")
JS = (SRC / "assets" / "site.js").read_text(encoding="utf-8")


PHONE_TOOL = """<div id="pv-tool">
<style>
#pv-open{position:fixed;left:16px;bottom:16px;z-index:9998;font:600 13px/1 system-ui,sans-serif;letter-spacing:.06em;text-transform:uppercase;
  background:#fff;color:#000;border:0;border-radius:999px;padding:12px 16px;cursor:pointer;box-shadow:0 4px 18px rgba(0,0,0,.5)}
#pv-overlay{position:fixed;inset:0;z-index:9999;background:rgba(0,0,0,.88);display:grid;place-items:center;gap:12px;align-content:center}
#pv-overlay[hidden]{display:none}
#pv-phone{width:390px;height:844px;border:10px solid #222;border-radius:44px;overflow:hidden;background:#000;transform-origin:top center}
#pv-phone iframe{width:390px;height:844px;border:0;display:block}
#pv-close{font:600 13px/1 system-ui,sans-serif;text-transform:uppercase;letter-spacing:.06em;background:#fff;color:#000;border:0;border-radius:999px;padding:10px 16px;cursor:pointer}
@media (max-width:600px){#pv-open{display:none}}
</style>
<button id="pv-open" type="button">Phone view</button>
<div id="pv-overlay" hidden><div id="pv-phone"><iframe name="pv-phone-frame" title="This page on a phone"></iframe></div>
<button id="pv-close" type="button">Close phone view</button></div>
<script>
(function(){
  if (window.name === "pv-phone-frame") { document.getElementById("pv-tool").remove(); return; }
  var o = document.getElementById("pv-overlay"), ph = document.getElementById("pv-phone"), f = ph.querySelector("iframe");
  var fit = function(){ var sc = Math.min(1, (window.innerHeight - 90) / 864); ph.style.transform = "scale(" + sc + ")";
    ph.style.marginBottom = (-(1 - sc) * 864) + "px"; };
  document.getElementById("pv-open").onclick = function(){ f.src = location.href; o.hidden = false; fit(); };
  document.getElementById("pv-close").onclick = function(){ o.hidden = true; f.src = "about:blank"; };
  window.addEventListener("resize", fit);
})();
</script>
</div>"""


def to_preview_links(doc):
    def fix(m):
        target = m.group(1)
        if target.startswith("//"):
            return m.group(0)
        path, _, frag = target.partition("#")
        name = "index" if path in ("", "/") else path.strip("/")
        return f'href="{name}.html' + (f"#{frag}" if frag else "") + '"'
    return re.sub(r'href="(/[^"]*)"', fix, doc)


def asset_v(name):
    """Short fingerprint of an asset, so browsers and the CDN fetch a changed file at once."""
    return hashlib.sha1((SRC / "assets" / name).read_bytes()).hexdigest()[:8]


PRIVATE = set()  # page paths with "private": true; left out of the live site for now


def hide_private(doc):
    for path in PRIVATE:
        doc = re.sub(r' · <a href="' + re.escape(path) + r'">[^<]*</a>', '', doc)
        doc = re.sub(r'<p[^>]*>(?:(?!</p>).)*href="' + re.escape(path) + r'[#"](?:(?!</p>).)*</p>\s*', '', doc, flags=re.S)
        if f'href="{path}"' in doc or f'href="{path}#' in doc:
            raise SystemExit(f"a link to private page {path} is still on a page")
    return doc


def page_doc(meta, body, posts, post=None, og_type="website", is_home=False):
    main = f'{header(meta["path"] if not post else "/blog-list")}\n<main id="main">\n{body}\n</main>\n{footer()}\n{action_bar()}\n{age_gate()}'
    if PREVIEW:
        head = (head_tags(meta, posts, post, og_type) + f"\n<style>{CSS}</style>")
        tail = f"<script>{JS}</script>\n{PHONE_TOOL}"
        if is_home:  # the published page gets its own document skeleton
            doc = (f'<meta name="claude:viewport-fit-sides" content="cover">\n{head}\n{main}\n{tail}\n')
        else:
            doc = (f'<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
                   f'<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
                   f'{head}\n</head>\n<body>\n{main}\n{tail}\n</body>\n</html>\n')
        return to_preview_links(doc)
    return hide_private(f'<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            f'{head_tags(meta, posts, post, og_type)}\n<link rel="stylesheet" href="/assets/style.css?v={asset_v("style.css")}">\n'
            f'</head>\n<body>\n{main}\n<script src="/assets/site.js?v={asset_v("site.js")}" defer></script>\n</body>\n</html>\n')


def post_body(p, posts):
    others = [q for q in posts if q["slug"] != p["slug"]][:2]
    more = "".join(post_card(q) for q in others)
    draft = ('<p class="note">Draft: shown in the preview only. Set <code>draft: false</code> to publish.</p>'
             if p["draft"] else "")
    return f'''<article class="section">
  <div class="wrap narrow stack-lg">
    <header class="post-head">
      <p class="breadcrumb"><a href="/">Home</a> / <a href="/blog-list">Blog</a></p>
      <h1>{esc(p["title"])}</h1>
      <p class="lede">{esc(p["description"])}</p>
      <p class="meta">By Electra Santiago · <time datetime="{p["date"]}">{nice_date(p["date"])}</time> · {p["minutes"]} min read</p>
      {draft}
    </header>
    <div class="prose post-body">{p["html"]}</div>
    <div class="card">
      <p class="eyebrow">Go deeper</p>
      <p>Book a <a href="/online-fetish-domination">private video session</a>, request a <a href="/online-fetish-domination#custom">custom video</a>, or join my <a href="{SITE["telegram"]}" rel="noopener">Telegram</a> for updates.</p>
    </div>
  </div>
</article>
<section class="section"><div class="wrap stack-lg"><h2>More from the blog</h2><div class="cards">{more}</div></div></section>'''


# ---------- site files ----------

def sitemap(entries):
    rows = "".join(f"<url><loc>{BASE}{p}</loc><lastmod>{d}</lastmod><priority>{pr}</priority></url>\n"
                   for p, d, pr in entries)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + rows + "</urlset>\n")


def feed(posts):
    items = "".join(
        f"<item><title>{esc(p['title'])}</title><link>{BASE}/{p['slug']}</link><guid>{BASE}/{p['slug']}</guid>"
        f"<pubDate>{dt.datetime.fromisoformat(p['date']).strftime('%a, %d %b %Y 00:00:00 +0000')}</pubDate>"
        f"<description>{esc(p['description'])}</description></item>\n" for p in posts[:20])
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>'
            f"<title>Electra Santiago</title><link>{BASE}/blog-list</link>"
            "<description>The Femdom Authority Blog</description><language>en</language>\n"
            f"{items}</channel></rss>\n")


ROBOTS = f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n"

HTACCESS = r"""# Hostinger / Apache
Options -MultiViews
AddDefaultCharset UTF-8
AddCharset UTF-8 .js .css .xml .txt
RewriteEngine On

# One canonical address: https, no www (only on the real domain, so a
# test copy on a temporary address isn't sent to the live site)
RewriteCond %{HTTP_HOST} ^www\.electrasantiago\.com$ [NC]
RewriteRule ^ https://electrasantiago.com%{REQUEST_URI} [L,R=301]
RewriteCond %{HTTP_HOST} ^electrasantiago\.com$ [NC]
RewriteCond %{HTTPS} off
RewriteRule ^ https://electrasantiago.com%{REQUEST_URI} [L,R=301]

# No X-Robots-Tag header here: a host check could mark the real pages noindex on Hostinger.
# Copies on other addresses are covered by each page's canonical link to electrasantiago.com.

# Pages that were merged into others
RewriteRule ^custom-femdom-video/?$ /online-fetish-domination#custom [NE,R=301,L]

# /page.html -> /page
RewriteCond %{THE_REQUEST} \s/+([^\s?]+?)\.html[\s?]
RewriteRule ^ /%1 [R=301,L]

# Serve /page from /page.html
RewriteCond %{REQUEST_FILENAME} !-d
RewriteCond %{REQUEST_FILENAME}.html -f
RewriteRule ^(.+?)/?$ $1.html [L]

ErrorDocument 404 /404.html

<IfModule mod_deflate.c>
  AddOutputFilterByType DEFLATE text/html text/css application/javascript application/xml image/svg+xml
</IfModule>
<IfModule mod_expires.c>
  ExpiresActive On
  ExpiresByType image/webp "access plus 1 year"
  ExpiresByType image/jpeg "access plus 1 year"
  ExpiresByType image/png "access plus 1 year"
  ExpiresByType text/css "access plus 1 week"
  ExpiresByType application/javascript "access plus 1 week"
</IfModule>
"""


def main():
    pages = load_pages()
    if not PREVIEW:
        PRIVATE.update(m["path"] for m in pages if m.get("private"))
        pages = [m for m in pages if not m.get("private")]
    posts = load_posts()
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    entries = []
    for meta in pages:
        is_home = meta["path"] == "/"
        name = "index" if is_home else meta["path"].strip("/")
        body = expand(meta["body"], posts)
        (OUT / f"{name}.html").write_text(page_doc(meta, body, posts, is_home=is_home), encoding="utf-8")
        entries.append((meta["path"], TODAY, meta.get("priority", "0.6")))

    for p in posts:
        meta = {"path": f"/{p['slug']}", "title": f"{p['title']} | Electra Santiago",
                "description": seo_desc(p["description"]), "schema": ["post", "breadcrumb"], "crumb": p["title"]}
        body = expand(post_body(p, posts), posts)
        (OUT / f"{p['slug']}.html").write_text(page_doc(meta, body, posts, post=p, og_type="article"),
                                               encoding="utf-8")
        if not p["draft"]:
            entries.append((f"/{p['slug']}", p.get("updated") or p["date"], "0.7"))

    nf = {"path": "/404", "title": "Page not found | Electra Santiago",
          "description": "This page doesn't exist.", "schema": []}
    nf_body = ('<section class="page-hero"><div class="wrap stack"><p class="eyebrow">404</p><h1>Lost, pet?</h1>'
               '<p class="lede">That page doesn’t exist. Start again from the beginning.</p>'
               '<div class="btn-row"><a class="btn btn-red" href="/">Go home</a>'
               '<a class="btn btn-ghost" href="/blog-list">Read the blog</a></div></div></section>')
    if PREVIEW and (SRC / "images").exists():
        shutil.copytree(SRC / "images", OUT / "images")
    if not PREVIEW:
        (OUT / "404.html").write_text(page_doc(nf, nf_body, posts).replace(
            '<meta name="robots" content="index, follow, max-image-preview:large">',
            '<meta name="robots" content="noindex">'), encoding="utf-8")
        (OUT / "assets").mkdir()
        shutil.copy(SRC / "assets" / "style.css", OUT / "assets" / "style.css")
        shutil.copy(SRC / "assets" / "site.js", OUT / "assets" / "site.js")
        if (SRC / "images").exists():
            shutil.copytree(SRC / "images", OUT / "images")
        (OUT / "sitemap.xml").write_text(sitemap(entries), encoding="utf-8")
        (OUT / "robots.txt").write_text(ROBOTS, encoding="utf-8")
        (OUT / "feed.xml").write_text(feed(posts), encoding="utf-8")
        (OUT / ".htaccess").write_text(HTACCESS, encoding="utf-8")
        # small server scripts, like the one that emails notes from the "Send a note" boxes
        if (SRC / "static").exists():
            for f in (SRC / "static").iterdir():
                shutil.copy(f, OUT / f.name)

    print(f"Built {len(pages)} pages and {len(posts)} posts into {OUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
