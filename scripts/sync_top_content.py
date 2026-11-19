#!/usr/bin/env python3
"""Build the static TOP and archive from verified news and merged changelog data."""
import html
import json
import re
from pathlib import Path
from urllib.parse import quote

DOCS = Path("docs")
index_path = DOCS / "index.html"
archive_path = DOCS / "updates.html"
changelog = (DOCS / "changelog.js").read_text(encoding="utf-8")
match = re.search(r"window\.SLOT_CHANGELOG=(\[.*?\]);", changelog, re.S)
if not match:
    raise SystemExit("Cannot locate SLOT_CHANGELOG")
entries = json.loads(match.group(1))
news = json.loads((DOCS / "industry-news.json").read_text(encoding="utf-8"))
verified = sorted(
    (x for x in news.get("items", []) if x.get("status") == "verified"
     and all(x.get(k) for k in ("title", "summary", "published_at", "source_url"))
     and x["source_url"].startswith("https://")),
    key=lambda x: x["published_at"], reverse=True,
)
e = lambda value: html.escape(str(value), quote=True)

def history_link(item, archive=False):
    url = "./" + quote(item["url"], safe="/#%-._~")
    date = item["date"]
    cls = ' class="changelog-entry"' if archive else ""
    return f'<a{cls} href="{e(url)}"><time datetime="{e(date)}">{e(date[5:].replace("-", "/"))}</time> {e(item["title"])}</a>'

def news_item(item):
    impact = f'<p>立ち回りへの影響：{e(item["impact"])}</p>' if item.get("impact") else ""
    return (f'<article class="industry-news-item"><span class="news-tag">{e(item.get("category", "業界ニュース"))}</span>'
            f'<time class="meta" datetime="{e(item["published_at"])}">{e(item["published_at"])} 公表</time>'
            f'<h3>{e(item["title"])}</h3><p>{e(item["summary"])}</p>{impact}'
            f'<a href="{e(item["source_url"])}" target="_blank" rel="noopener noreferrer">一次情報・確認元を見る</a></article>')

top = index_path.read_text(encoding="utf-8")
top = re.sub(r'(<div class="site-changelog-scroll" id="site-changelog-items"[^>]*>)[\s\S]*?(</div><p class="site-changelog-archive">)',
    lambda m: m.group(1) + "\n" + "\n".join(history_link(x) for x in entries[:8]) + "\n" + m.group(2),
    top, count=1)
news_html = "\n".join(news_item(x) for x in verified[:5]) or '<p class="meta">確認済みニュースを準備中です。</p>'
top = re.sub(r'(<div id="industry-news-list"[^>]*>)[\s\S]*?(</div></section>\s*<section class="discovery" id="find-machine">)',
    lambda m: m.group(1) + '<div class="industry-news-list" tabindex="0" aria-label="業界ニュース一覧（スクロールできます）">' + news_html + '</div>' + m.group(2),
    top, count=1)
if not all(x in top for x in ("site-changelog-items", "industry-news-list")):
    raise SystemExit("TOP section verification failed")
if top != index_path.read_text(encoding="utf-8"):
    index_path.write_text(top, encoding="utf-8")

archive = archive_path.read_text(encoding="utf-8")
archive = re.sub(r'(<div id="changelog-archive-items">)[\s\S]*?(</div><nav id="changelog-pagination")',
    lambda m: m.group(1) + "\n" + "\n".join(history_link(x, True) for x in entries[:20]) + "\n" + m.group(2),
    archive, count=1)
if archive != archive_path.read_text(encoding="utf-8"):
    archive_path.write_text(archive, encoding="utf-8")
print(f"Synced TOP: {min(len(entries),8)} history, {min(len(verified),5)} news; archive: {min(len(entries),20)}")
