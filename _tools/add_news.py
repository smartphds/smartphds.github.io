"""Add a weekly industry news roundup to the SmartPhDs site.

Usage (run from the site root):
  python3 _tools/add_news.py ROUNDUP.json

ROUNDUP.json:
{
  "date": "2026-10-24",                       # publication date, also the page slug
  "title": "Industry news for PhDs: week of October 24, 2026",
  "description": "Under 160 characters for search results.",
  "intro": "One or two sentences.",
  "items": [
    {"headline": "...", "source": "BioSpace", "source_url": "https://...", "published": "October 8, 2026",
     "summary": "What happened, in our own words, 2-4 sentences.",
     "meaning": "What it means for PhDs, 1-3 sentences."}
  ]
}
Builds news/DATE.html, updates news/index.html (newest first), the homepage "latest news" link and sitemap.xml.
"""
import html, json, re, sys, pathlib, datetime

data = json.loads(pathlib.Path(sys.argv[1]).read_text())
root = pathlib.Path(".")
date = data["date"]; datetime.date.fromisoformat(date)
assert 4 <= len(data["items"]) <= 10, "use 4 to 10 news items"
e = lambda s: html.escape(s, quote=True)

items_html = []
for i, it in enumerate(data["items"], 1):
    assert it["source_url"].startswith("https://"), "every item needs an https source link"
    items_html.append(f'''      <section class="news-item">
        <p class="label">{i:02d} · {e(it["source"])} · {e(it["published"])}</p>
        <h2>{e(it["headline"])}</h2>
        <p>{e(it["summary"])}</p>
        <p class="news-meaning"><strong>What it means for you:</strong> {e(it["meaning"])}</p>
        <p class="news-source"><a href="{e(it["source_url"])}" rel="noopener noreferrer">Read the source: {e(it["source"])} →</a></p>
      </section>''')

nice = datetime.date.fromisoformat(date).strftime("%B %-d, %Y")
body = f'''<article>
    <div class="page-head">
      <p class="label">Industry news · {nice}</p>
      <h1>{e(data["title"])}</h1>
      <p class="lede">{e(data["intro"])}</p>
    </div>
    <div class="prose news-list">
{chr(10).join(items_html)}
      <p class="news-note">Summaries are written by SmartPhDs from the linked reporting. Follow each link for the full story.</p>
      <div class="callout" style="margin-top:2.6rem">
        <h3>Turn the news into a plan</h3>
        <p>Find the industry role that fits you, then make sure your resume speaks the language recruiters search for.</p>
        <div class="btn-row"><a class="btn" href="../#role-finder">Take the role finder</a><a class="btn ghost" href="../checklist.html">Open the free checklist</a></div>
      </div>
    </div>
  </article>'''

# Build from the guide template, pointing nav at News
tpl = (root / "guides/industry-resume-for-phds.html").read_text()
page = re.sub(r"  <article>.*?</article>", lambda m: "  " + body, tpl, count=1, flags=re.S)
page = page.replace('<a href="./" aria-current="page">Blog</a>', '<a href="../guides/">Blog</a>')
page = page.replace('<a href="../news/">News</a>', '<a href="./" aria-current="page">News</a>')
title, desc, url = data["title"], data["description"], f"https://smartphds.com/news/{date}.html"
page = re.sub(r"<title>.*?</title>", f"<title>{e(title)} | SmartPhDs</title>", page, count=1)
page = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{e(desc)}">', page, count=1)
page = re.sub(r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="{url}">', page, count=1)
page = re.sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{e(title)}">', page, count=1)
src = (root / "_tools/add_guide.py").read_text()
ns = {"re": re, "html": html, "datetime": datetime}
exec(src[src.index("import json as _json"):src.index("slug, title, desc, minutes, body_file")], ns)
page = ns["seo_head"](page, title, desc, url, "News", "https://smartphds.com/news/", date)
page = page.replace('"@type": "Article"', '"@type": "NewsArticle"', 1)
(root / "news").mkdir(exist_ok=True)
(root / f"news/{date}.html").write_text(page)

# news/index.html
idx = root / "news/index.html"
row = f'    <li><a href="{date}.html">{e(title)}</a><span class="label">{nice}</span></li>'
if idx.exists():
    t = idx.read_text()
    if f'href="{date}.html"' not in t:
        t, n = re.subn(r'(<ul class="guides news-index"[^>]*>)', lambda m: m.group(1) + "\n" + row, t, count=1)
        assert n == 1, "could not find the news list in news/index.html"
else:
    g = (root / "guides/index.html").read_text()
    t = re.sub(r'<main class="wrap">.*?</main>', lambda m: f'''<main class="wrap">
  <div class="page-head">
    <p class="label">Industry news</p>
    <h1>What's happening in pharma and biotech careers.</h1>
    <p class="lede">A weekly roundup of hiring, layoffs, job-market data, AI and policy news, with what each story means for PhDs heading into industry.</p>
  </div>
  <ul class="guides news-index" style="padding-bottom:4rem">
{row}
  </ul>
</main>''', g, flags=re.S)
    t = t.replace('<a href="./" aria-current="page">Blog</a>', '<a href="../guides/">Blog</a>')
    t = t.replace('<a href="../news/">News</a>', '<a href="./" aria-current="page">News</a>')
    t = re.sub(r"<title>.*?</title>", "<title>Industry News for PhDs: Pharma and Biotech Jobs | SmartPhDs</title>", t, count=1)
    t = re.sub(r'<meta name="description" content="[^"]*">', '<meta name="description" content="Weekly pharma and biotech career news for PhDs: hiring and layoffs, job-market data, AI in drug development and policy, with what it means for you.">', t, count=1)
    t = re.sub(r'<link rel="canonical" href="[^"]*">', '<link rel="canonical" href="https://smartphds.com/news/">', t, count=1)
idx.write_text(t)

# homepage: latest news link under the blog list
h = (root / "index.html").read_text()
link = f'<p class="compare-link latest-news"><a href="news/{date}.html">Latest industry news: {e(title)} →</a></p>'
if 'class="compare-link latest-news"' in h:
    h = re.sub(r'<p class="compare-link latest-news">.*?</p>', link, h, count=1)
else:
    h = h.replace('''        </ul>
      </div>
    </div>
  </section>

  <section class="cta-photo">''', f'''        </ul>
        {link}
      </div>
    </div>
  </section>

  <section class="cta-photo">''', 1)
(root / "index.html").write_text(h)

# sitemap
sm = root / "sitemap.xml"; s = sm.read_text()
for u in ["https://smartphds.com/news/", url]:
    if f"<loc>{u}</loc>" not in s:
        s = s.replace("</urlset>", f"  <url><loc>{u}</loc><lastmod>{date}</lastmod></url>\n</urlset>")
sm.write_text(s)
print("added", f"news/{date}.html")
