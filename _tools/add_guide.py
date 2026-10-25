"""Add a new guide to the SmartPhDs site.

Usage (run from the site root):
  python3 _tools/add_guide.py SLUG "Title" "Meta description" MINUTES BODY_FILE

BODY_FILE holds only the <article>...</article> block, written like the existing guides.
The script builds guides/SLUG.html from the template guide, lists it first on the guides
page and the homepage, removes any matching "Soon" placeholder, and adds it to sitemap.xml.
Folders starting with "_" are not published by GitHub Pages.
"""
import html, re, sys, datetime, pathlib


import json as _json

def seo_head(page, title, desc, url, section, section_url, published=None):
    """Replace per-page SEO tags: og:url, og:description, and Article + Breadcrumb structured data."""
    today = published or datetime.date.today().isoformat()
    page = re.sub(r'\n<meta property="og:url" content="[^"]*">', "", page)
    page = re.sub(r'\n<meta property="og:description" content="[^"]*">', "", page)
    page = re.sub(r'\n<script type="application/ld\+json">.*?</script>', "", page, flags=re.S)
    ld = [{"@context": "https://schema.org", "@type": "Article", "headline": title, "description": desc,
           "datePublished": today, "dateModified": today, "mainEntityOfPage": url,
           "image": "https://smartphds.com/assets/og-image.png",
           "author": {"@type": "Organization", "name": "SmartPhDs", "url": "https://smartphds.com"},
           "publisher": {"@type": "Organization", "name": "SmartPhDs", "logo": {"@type": "ImageObject", "url": "https://smartphds.com/assets/apple-touch-icon.png"}}},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://smartphds.com/"},
              {"@type": "ListItem", "position": 2, "name": section, "item": section_url},
              {"@type": "ListItem", "position": 3, "name": title, "item": url}]}]
    tags = (f'\n<meta property="og:url" content="{url}">'
            f'\n<meta property="og:description" content="{html.escape(desc, quote=True)}">'
            f'\n<script type="application/ld+json">{_json.dumps(ld)}</script>')
    return page.replace('\n<meta property="og:type" content="article">', tags + '\n<meta property="og:type" content="article">', 1)

slug, title, desc, minutes, body_file = sys.argv[1:6]
root = pathlib.Path(".")
template = (root / "guides/industry-resume-for-phds.html").read_text()
body = pathlib.Path(body_file).read_text().strip()
assert body.startswith("<article>") and body.endswith("</article>"), "BODY_FILE must be one <article> block"
assert re.fullmatch(r"[a-z0-9-]+", slug), "slug must be lowercase letters, digits and hyphens"
target = root / "guides" / f"{slug}.html"
assert not target.exists(), f"{target} already exists"

t, d = html.escape(title, quote=True), html.escape(desc, quote=True)
page = template
page = re.sub(r"<title>.*?</title>", f"<title>{t} | SmartPhDs</title>", page, count=1)
page = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{d}">', page, count=1)
page = re.sub(r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="https://smartphds.com/guides/{slug}.html">', page, count=1)
page = re.sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{t}">', page, count=1)
page = re.sub(r"  <article>.*?</article>", lambda m: "  " + body, page, count=1, flags=re.S)
assert "<script" not in body and "onclick" not in body, "no scripts in articles"
page = seo_head(page, title, desc, f"https://smartphds.com/guides/{slug}.html", "Blog", "https://smartphds.com/guides/")
target.write_text(page)

def first_words(s):
    """Short key for matching placeholders: the part before any colon, letters and digits only."""
    return re.sub(r"[^a-z0-9]", "", s.split(":")[0].lower())

# guides/index.html: new item first, drop a matching "Soon" placeholder
gi = root / "guides/index.html"; g = gi.read_text()
g = re.sub(r'\s*<li class="upcoming"><span>([^<]*)</span><span class="label">Soon</span></li>',
           lambda m: "" if first_words(m.group(1)) == first_words(title) else m.group(0), g)
g = g.replace('<ul class="guides" style="padding-bottom:4rem">',
              f'<ul class="guides" style="padding-bottom:4rem">\n    <li><a href="{slug}.html">{t}</a><span class="label">{minutes} min</span></li>', 1)
gi.write_text(g)

# homepage: newest first, keep at most 4 rows, drop "Soon" rows before published ones
hi = root / "index.html"; h = hi.read_text()
m = re.search(r'(<ul class="role-list guide-list">)(.*?)(\n        </ul>)', h, re.S)
rows = re.findall(r"\n          <li>.*?</li>", m.group(2))
rows = [r for r in rows if first_words(re.sub("<[^>]+>", "", r)) != first_words(title)]
new_row = f'\n          <li><a href="guides/{slug}.html">{t}</a><span>{minutes} min</span></li>'
published = [r for r in rows if "<a " in r]; soon = [r for r in rows if "<a " not in r]
rows = ([new_row] + published + soon)[:4]
h = h[:m.start(2)] + "".join(rows) + h[m.end(2):]
hi.write_text(h)

# sitemap
sm = root / "sitemap.xml"; s = sm.read_text()
today = datetime.date.today().isoformat()
s = s.replace("</urlset>", f"  <url><loc>https://smartphds.com/guides/{slug}.html</loc><lastmod>{today}</lastmod></url>\n</urlset>")
sm.write_text(s)
print("added", target)
