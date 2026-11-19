# Blog posts

One file per post. The file name is the post's web address:
`my-post-title.md` is published at `https://electrasantiago.com/my-post-title`.

## Adding a weekly post

1. Copy any post in this folder and rename it (lowercase words joined by hyphens).
2. Fill in the top block:

```
---
title: "The headline as it should appear"
date: 2026-12-01
description: "One or two sentences, about 150 characters. Shown in Google results and link previews."
draft: false
---
```

3. Write the post below it in Markdown: `### Sub-heading`, `**bold**`, `- list item`,
   `[link text](/online-fetish-domination)`.
4. Optional extras in the top block: `image: /images/my-photo.jpg` (social preview image)
   and `updated: 2026-12-08` (if you revise it later).
5. Run `python3 build.py`. The post appears on the blog page, the home page (if it's
   one of the newest three), the sitemap and the RSS feed, with its own search title,
   description, Open Graph tags and article structured data.

`draft: true` keeps a post out of the live site and sitemap; it still shows in the preview.

A header photo: put a line `[image: description of the photo]` where it should go, and save
the photo as `src/images/<file-name-of-the-post>.jpg`.
