"""Read public X recent search safely and publish IDs only (never Post text).

This script is optional. Without X_COLLECTION_ENABLED=true and a secret bearer
token, no paid API requests are sent. Intended for a public GitHub Actions job.
Output is a small JSON snapshot for a static GitHub Pages viewer.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

FEED_SCHEMA = 1
X_ENDPOINT = "https://api.x.com/2/tweets/search/recent"
MACHINES = {
    "seiya": '(聖闘士星矢 OR 黄金十二宮) (スマスロ OR パチスロ)',
    "ggo": '"ガンゲイル・オンライン" (スマスロ OR スロット)',
    "kabaneri": '"カバネリ" "海門" (スマスロ OR パチスロ)',
    "tokyoghoul": '(東京喰種 OR 東京グール) (スマスロ OR パチスロ)',
    "otome5": '(戦国乙女5 OR "乙女5") (スマスロ OR パチスロ)',
    "monhun": '"モンハンライズ" -サンブレイク (スマスロ OR パチスロ)',
    "sunbreak": '(モンハンサンブレイク OR "ライズ サンブレイク") (スマスロ OR パチスロ)',
    "monkey5": '("モンキーターンV" OR "モンキーターン5") (スマスロ OR スロット)',
    "sencolle5": '("戦コレ5" OR "戦国コレクション5") (スロット OR パチスロ)',
    "kanokari": '(かのかり OR "彼女、お借りします") (スマスロ OR パチスロ)',
}
X_ID = re.compile(r"^[0-9]{10,25}$")
MAX_POSTS_PER_MACHINE = 12
MAX_CALLS_PER_RUN = 3


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_date(s: str) -> datetime | None:
    if not isinstance(s, str) or len(s) > 40:
        return None
    try:
        d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return d.astimezone(timezone.utc) if d.tzinfo else None
    except (ValueError, OverflowError):
        return None


def safe_record(machine: str, raw: object, now: datetime) -> dict | None:
    if not isinstance(raw, dict):
        return None
    identifier = raw.get("id")
    posted_at = raw.get("created_at", raw.get("posted_at"))
    if not isinstance(identifier, str) or not X_ID.fullmatch(identifier):
        return None
    date = parse_date(posted_at)
    if date is None or not now - timedelta(days=7) <= date <= now + timedelta(minutes=5):
        return None
    return {
        "id": identifier,
        "posted_at": iso(date),
        "url": "https://x.com/i/status/" + identifier,
    }


def normalize_feed(raw: object, now: datetime) -> dict:
    result = {"schema": FEED_SCHEMA, "status": "not_configured",
              "generated_at": None, "machines": {}}
    for machine in MACHINES:
        result["machines"][machine] = {"fetched_at": None, "posts": []}
    if not isinstance(raw, dict) or raw.get("schema") != FEED_SCHEMA:
        return result
    if raw.get("status") in ("active", "not_configured"):
        result["status"] = raw["status"]
    result["generated_at"] = raw.get("generated_at") if parse_date(raw.get("generated_at")) else None
    entries = raw.get("machines", {})
    if not isinstance(entries, dict):
        return result
    for machine in MACHINES:
        obj = entries.get(machine)
        if not isinstance(obj, dict):
            continue
        fetched = obj.get("fetched_at")
        if parse_date(fetched) and parse_date(fetched) <= now + timedelta(minutes=5):
            result["machines"][machine]["fetched_at"] = iso(parse_date(fetched))
        posts = obj.get("posts", [])
        if not isinstance(posts, list):
            continue
        seen = set()
        for item in posts:
            sanitized = safe_record(machine, item, now)
            if not sanitized or sanitized["id"] in seen:
                continue
            seen.add(sanitized["id"])
            result["machines"][machine]["posts"].append(sanitized)
        result["machines"][machine]["posts"].sort(key=lambda p: p["posted_at"], reverse=True)
        result["machines"][machine]["posts"] = result["machines"][machine]["posts"][:MAX_POSTS_PER_MACHINE]
    return result


def query_for_machine(machine: str) -> str:
    return MACHINES[machine] + " lang:ja -is:retweet"


def select_machines(now: datetime, max_calls: int = MAX_CALLS_PER_RUN) -> list[str]:
    """Rotate three machine queries each day; no burst over the call cap."""
    max_calls = min(max(0, max_calls), MAX_CALLS_PER_RUN)
    keys = list(MACHINES)
    start = (now.date().toordinal() * MAX_CALLS_PER_RUN) % len(keys)
    return [keys[(start + i) % len(keys)] for i in range(max_calls)]


def fetch_recent(machine: str, bearer: str, opener=urlopen) -> list[dict]:
    if machine not in MACHINES:
        raise ValueError("unknown_machine")
    query = urlencode({
        "query": query_for_machine(machine),
        "max_results": 10,
        "tweet.fields": "created_at",
    })
    request = Request(
        X_ENDPOINT + "?" + query,
        headers={
            "Authorization": "Bearer " + bearer,
            "User-Agent": "SlotIntelligenceEvidenceIndexer/1.0",
            "Accept": "application/json",
        },
    )
    try:
        with opener(request, timeout=20) as response:
            payload = response.read(200000)
    except (HTTPError, URLError, TimeoutError) as exc:
        # Do not show the bearer token or request headers in logs.
        raise RuntimeError("X_recent_search_request_failed") from None
    try:
        data = json.loads(payload)
    except (ValueError, UnicodeDecodeError) as exc:
        raise RuntimeError("X_response_not_json") from exc
    if not isinstance(data, dict) or not isinstance(data.get("data", []), list):
        raise RuntimeError("X_response_shape_invalid")
    return data.get("data", [])


def build_snapshot(existing: object, responses: dict[str, list], now: datetime) -> dict:
    feed = normalize_feed(existing, now)
    for machine, response in responses.items():
        if machine not in MACHINES or not isinstance(response, list):
            raise ValueError("unexpected_machine_or_posts")
        entries = {p["id"]: p for p in feed["machines"][machine]["posts"]}
        for item in response:
            sanitized = safe_record(machine, item, now)
            if sanitized:
                entries[sanitized["id"]] = sanitized
        latest = sorted(entries.values(), key=lambda p: p["posted_at"], reverse=True)
        feed["machines"][machine] = {
            "fetched_at": iso(now),
            "posts": latest[:MAX_POSTS_PER_MACHINE],
        }
    feed["generated_at"] = iso(now)
    feed["status"] = "active" if responses else feed["status"]
    return feed


def run(source: Path, enabled: bool, bearer: str, now: datetime, opener=urlopen) -> bool:
    if not enabled:
        print("X auto collection is disabled; no API requests made.")
        return False
    if not bearer or len(bearer) < 10:
        print("X bearer token is not configured; no API requests made.")
        return False
    if source.exists():
        if source.stat().st_size > 500_000:
            raise RuntimeError("feed_too_large")
        existing = json.loads(source.read_text(encoding="utf-8"))
    else:
        existing = {}
    machines = select_machines(now)
    responses: dict[str, list] = {}
    for machine in machines:
        responses[machine] = fetch_recent(machine, bearer, opener=opener)
    snapshot = build_snapshot(existing, responses, now)
    source.parent.mkdir(parents=True, exist_ok=True)
    temporary = source.with_name(source.name + ".tmp")
    temporary.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(source)
    print("Updated X feed for", len(machines), "machines; URLs and IDs only.")
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("docs/x-feed.json"))
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        obj = json.loads(args.output.read_text(encoding="utf-8"))
        result = normalize_feed(obj, utc_now())
        if result["schema"] != FEED_SCHEMA:
            raise SystemExit("schema_invalid")
        print("Feed JSON shape read successfully.")
        return
    enabled = os.environ.get("X_COLLECTION_ENABLED") == "true"
    bearer = os.environ.get("X_API_BEARER_TOKEN", "")
    run(args.output, enabled, bearer, utc_now())


if __name__ == "__main__":
    main()
