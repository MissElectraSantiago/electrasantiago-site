# electrasantiago.com

Static site. Edit files in `src/` on the `main` branch.

How it goes live: every push to `main` runs the "Build site" GitHub Action, which builds the site and puts the finished files on the `live` branch. Hostinger deploys the `live` branch to `public_html`. Never edit `live` by hand; it is replaced on every build.

To build locally: `pip install markdown`, then `python3 build.py` (output in `public/`).

- `src/site.json`: links, nav, footer, contact email, Telegram, form ids and form endpoints.
- `src/pages/*.html`: one file per page; the `<!--meta {...} -->` block sets the URL, search title, description and structured data.
- `src/posts/*.md`: blog posts, one per file (see `src/posts/README.md`).
- `src/images/`: photos, named as the placeholders show (e.g. `gallery-01.jpg`, `about-portrait.jpg`, `og-share.jpg` for link previews). A missing photo shows a placeholder.
- `src/assets/`: styles and the small script (menu, 18+ notice, copy buttons, forms).

`python3 build.py --preview` builds a self-contained preview into `preview/`.
