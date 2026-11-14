#!/usr/bin/env python3
"""Collect only public machine catalog metadata and public change headlines.

Never copies paid content, infers targeting thresholds, or publishes machine EV.
No dependencies; HTTPS allowlist, response limits, and graceful failure.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

DOMAIN = "pachiseven.jp"
LIST_URL = "https://pachiseven.jp/machines/list_machine/slot.html"
UPDATE_URL = "https://pachiseven.jp/machines/index.html"
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs" / "auto-machine-discovery.json"
DATE_RE = re.compile(r"(20\d{2})[./年](\d{1,2})[./月](\d{1,2})")
MACHINE_PATH = re.compile(r"^/machines/(\d{3,6})/?$")
SOURCE_PREFIX = "https://" + DOMAIN


def normalize_url(href: str) -> str | None:
    url = urllib.parse.urljoin(SOURCE_PREFIX, href or "")
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != DOMAIN or parsed.port not in (None, 443):
        return None
    if not parsed.path.startswith("/machines/"):
        return None
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


class LinkParser(HTMLParser):
    """Extract anchor text and img-alt, excluding scripts, without JS execution."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.anchors: list[tuple[str, str]] = []
        self.href: str | None = None
        self.parts: list[str] = []
        self.ignored = 0

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag in {"script", "style", "noscript"}:
            self.ignored += 1
        if tag == "a" and not self.ignored and self.href is None:
            self.href = values.get("href", "")
            self.parts = []
        if tag == "img" and self.href is not None and not self.ignored:
            self.parts.append(values.get("alt", ""))

    def handle_data(self, data):
        if self.href is not None and not self.ignored:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"} and self.ignored:
            self.ignored -= 1
        if tag == "a" and self.href is not None:
            self.anchors.append((self.href, clean(" ".join(self.parts))))
            self.href = None
            self.parts = []


def parse_catalog(html: str) -> list[dict]:
    parser = LinkParser()
    parser.feed(html)
    results = []
    seen = set()
    for href, label in parser.anchors:
        url = normalize_url(href)
        if not url or not MACHINE_PATH.fullmatch(urllib.parse.urlsplit(url).path):
            continue
        if url in seen or not label:
            continue
        # The catalog labels include a factual maker line; do not republish article text.
        name, _, maker = label.partition("メーカー名：")
        name, maker = clean(name), clean(maker)
        if not 3 <= len(name) <= 110:
            continue
        if "新台情報" in name or "機種情報" in name or name == "パチスロ":
            continue
        seen.add(url)
        results.append({"id": urllib.parse.urlsplit(url).path.rsplit("/", 1)[1],
                        "name": name, "maker": maker[:65], "url": url})
    if len(results) < 3:
        raise ValueError("Catalog parse returned fewer than 3 machines; stop without publishing")
    return results[:70]


def parse_updates(html: str) -> list[dict]:
    parser = LinkParser()
    parser.feed(html)
    results, seen = [], set()
    for href, label in parser.anchors:
        url = normalize_url(href)
        if not url or not label:
            continue
        match = DATE_RE.search(label[:20])
        if not match:
            continue
        date = f"{int(match[1]):04d}-{int(match[2]):02d}-{int(match[3]):02d}"
        try:
            dt.date.fromisoformat(date)
        except ValueError:
            continue
        headline = clean(label[match.end():].lstrip("　 -:"))
        if not 3 <= len(headline) <= 95:
            continue
        # The same page also shows new-machine release dates and pachinko news.
        # Only article update announcements should become the change feed.
        if "メーカー名" in headline or not ("更新" in headline or "アップ" in headline):
            continue
        # Keep brief change labels, not article paragraphs, and never invent a claim.
        key = (url, date, headline)
        if key in seen:
            continue
        seen.add(key)
        results.append({"date": date, "headline": headline, "url": url})
    results.sort(key=lambda x: x["date"], reverse=True)
    return results[:70]


def fetch(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "SlotIntelResearchBot/1.0 (+public-source-link-collector)",
                 "Accept": "text/html; charset=utf-8"},
    )
    with urllib.request.urlopen(req, timeout=15) as response:
        resolved = response.geturl()
        if not normalize_url(resolved):
            raise ValueError("Unexpected origin or redirect")
        if response.status != 200:
            raise ValueError(f"HTTP {response.status}")
        raw = response.read(1_600_001)
        if len(raw) > 1_600_000:
            raise ValueError("Response unexpectedly large")
    return raw.decode("utf-8", errors="replace")


def build(previous: dict, catalog: list[dict], updates: list[dict], today: str) -> dict:
    existing = {str(row.get("id")): row for row in previous.get("machines", [])}
    machines = []
    for row in catalog:
        old = existing.get(row["id"], {})
        machines.append({**row, "first_seen": old.get("first_seen", today)})
    # The homepage also reports pachinko news. Admit catalog machines, plus clearly
    # slot-labeled archived headlines; never silently mix pachinko with slot updates.
    catalog_urls = {row["url"] for row in machines}
    slot_label = re.compile(r"スマスロ|パチスロ|スロット|Ｌパチスロ|Lパチスロ", re.I)
    updates = [row for row in updates if row["url"] in catalog_urls or slot_label.search(row["headline"])]
    previous_updates = {(
        x.get("date"), x.get("headline"), x.get("url")
    ): x for x in previous.get("updates", [])
        if "メーカー名" not in x.get("headline", "")}
    merged = list(previous_updates.values())
    keys = set(previous_updates)
    for entry in updates:
        key = (entry["date"], entry["headline"], entry["url"])
        if key not in keys:
            merged.append(entry)
            keys.add(key)
    merged.sort(key=lambda x: (x["date"], x["url"], x["headline"]), reverse=True)
    # Only source links and update headings; NOT unverified targeting information.
    return {
        "schema": 1,
        "source": "パチ7（一般公開の機種カタログ・更新見出し）",
        "catalog_url": LIST_URL,
        "news_url": UPDATE_URL,
        "note": "公開情報のタイトル・メーカー名・更新見出しを自動収集。狙い目、当選確率、期待値、設定差、優遇・冷遇を自動推定しません。記事本文は転載しません。",
        "machines": machines[:70],
        "updates": merged[:100],
    }


def run(output: Path, date: str):
    old = json.loads(output.read_text(encoding="utf-8")) if output.exists() else {}
    if not isinstance(old, dict):
        raise ValueError("Existing JSON must be an object")
    catalog = parse_catalog(fetch(LIST_URL))
    # A temporary failure of the updates page should not erase saved news.
    try:
        updates = parse_updates(fetch(UPDATE_URL))
    except Exception as exc:
        print(f"Update listing unavailable; preserving history: {exc}", file=sys.stderr)
        updates = []
    next_data = build(old, catalog, updates, date)
    if old == next_data:
        print(f"No catalog change ({len(catalog)} machines; {len(next_data['updates'])} saved updates)")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(next_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    old_ids = {x.get("id") for x in old.get("machines", [])}
    print(f"Updated catalog. New IDs: {[x['id'] for x in catalog if x['id'] not in old_ids]}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--date", default=dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).date().isoformat())
    args = parser.parse_args()
    run(args.output, args.date)
