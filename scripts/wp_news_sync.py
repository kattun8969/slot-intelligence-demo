#!/usr/bin/env python3
"""Create a standard WordPress news draft from an editor-reviewed JSON file.

Never publishes, modifies existing posts, or touches custom machine post types.
"""
import argparse
import base64
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parent.parent
QUEUE = (ROOT / "wordpress-queue" / "news").resolve()
HOST = "kajiplus.info"
SLUG = re.compile(r"^news-[a-z0-9]+(?:-[a-z0-9]+)*$")
DATE = re.compile(r"^20\d\d-\d\d-\d\d$")


def read_article(filename):
    path = (ROOT / filename).resolve()
    if not path.is_relative_to(QUEUE) or path.suffix != ".json":
        raise ValueError("Article must be a JSON file in wordpress-queue/news/")
    article = json.loads(path.read_text(encoding="utf-8"))
    required = ("slug", "title", "content_html", "source_url", "source_checked_at", "announced_on")
    if not isinstance(article, dict) or any(not isinstance(article.get(k), str) or not article[k].strip() for k in required):
        raise ValueError("Missing required string fields in article")
    if not SLUG.fullmatch(article["slug"]):
        raise ValueError("Slug must use news- plus lowercase English letters, numbers and hyphens")
    if len(article["title"]) > 140 or len(article["content_html"]) > 50000:
        raise ValueError("Title or content exceeds limits")
    for k in ("source_checked_at", "announced_on"):
        if not DATE.fullmatch(article[k]):
            raise ValueError("Dates must use YYYY-MM-DD")
    source = urlparse(article["source_url"])
    if source.scheme != "https" or not source.hostname:
        raise ValueError("An HTTPS source URL is required")
    if "<script" in article["content_html"].lower():
        raise ValueError("Script tags are not allowed")
    if article.get("editor_reviewed") is not True:
        raise ValueError("Editor review flag is required before staging")
    return article


def request(base, auth, path, method="GET", payload=None):
    headers = {"Authorization": "Basic " + auth, "Accept": "application/json"}
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json; charset=utf-8"
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = Request(base + path, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=25) as response:
            return response.status, json.load(response)
    except HTTPError as exc:
        # Never print server error bodies, credentials or article text.
        raise RuntimeError("WordPress API returned HTTP " + str(exc.code)) from None
    except (URLError, TimeoutError):
        raise RuntimeError("WordPress API connection failed") from None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True)
    args = parser.parse_args()
    article = read_article(args.file)
    base = os.environ.get("WP_BASE_URL", "").rstrip("/")
    user = os.environ.get("WP_USERNAME", "")
    pw = os.environ.get("WP_APP_PASSWORD", "")
    if not all((base, user, pw)) or urlparse(base).scheme != "https" or urlparse(base).hostname != HOST:
        raise ValueError("WP configuration is missing or target host is not approved")
    auth = base64.b64encode((user + ":" + pw).encode("utf-8")).decode("ascii")
    _, me = request(base, auth, "/wp-json/wp/v2/users/me?context=edit")
    if not isinstance(me, dict) or not me.get("id"):
        raise RuntimeError("WordPress authentication failed")
    qs = urlencode({"slug": article["slug"], "status": "any", "context": "edit", "per_page": 20})
    _, existing = request(base, auth, "/wp-json/wp/v2/posts?" + qs)
    if existing:
        print("Skipped: matching WordPress slug already exists (no overwrite)")
        return
    html = article["content_html"].strip()
    html += ('<p><small>発表日：' + article["announced_on"] +
             '／出典確認日：' + article["source_checked_at"] +
             '　出典：<a href="' + article["source_url"].replace("&", "&amp;").replace('"', "&quot;") +
             '" target="_blank" rel="noopener noreferrer">公式・一次情報</a></small></p>')
    payload = {"title": article["title"], "slug": article["slug"],
               "content": html, "status": "draft"}
    status, post = request(base, auth, "/wp-json/wp/v2/posts", "POST", payload)
    if status != 201 or post.get("status") != "draft" or not post.get("id"):
        raise RuntimeError("Draft was not confirmed")
    _, reread = request(base, auth, "/wp-json/wp/v2/posts/" + str(post["id"]) + "?context=edit")
    if reread.get("status") != "draft" or reread.get("slug") != article["slug"]:
        raise RuntimeError("WordPress draft verification failed")
    print("Verified WordPress NEWS DRAFT ID:", post["id"], "(not published)")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        # Avoid output of raw article contents / authentication material.
        print("News draft sync failed:", type(exc).__name__, str(exc)[:180], file=sys.stderr)
        sys.exit(1)
