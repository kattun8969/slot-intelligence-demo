#!/usr/bin/env python3
"""Build a reviewable changelog from merged machine-page commits; keep older entries."""
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

FILE = Path("docs/changelog.js")
source = FILE.read_text(encoding="utf-8")
match = re.search(r"window\.SLOT_CHANGELOG=(\[.*?\]);", source, re.S)
if not match:
    raise SystemExit("Missing changelog data")
existing = json.loads(match.group(1))
seen = {e.get("commit", "") for e in existing if e.get("commit")}
result = []
raw = subprocess.check_output(
    ["git", "log", "--first-parent", "--format=%H%x1f%cI%x1f%s", "--name-only", "-n", "120", "HEAD"],
    text=True,
)
for block in re.split(r"\n(?=[0-9a-f]{40}\x1f)", raw.strip()):
    lines = block.splitlines()
    if not lines or "\x1f" not in lines[0]:
        continue
    sha, when, subject = lines[0].split("\x1f", 2)
    if sha[:8] in seen:
        continue
    paths = [p for p in lines[1:] if p.startswith("docs/machines/") and p.endswith(".html")]
    if not paths:
        continue
    # One meaningful entry per machine per commit; never expose raw internal metadata changes.
    for path in sorted(set(paths)):
        title = subject.strip()
        if re.match(r"^(Merge pull request|Auto-update|chore:|ci:|test:)", title, re.I):
            continue
        title = re.sub(r"\s*\(#\d+\)$", "", title)
        if not title or len(title) > 110:
            continue
        day = datetime.fromisoformat(when.replace("Z", "+00:00")).astimezone(timezone.utc).strftime("%Y-%m-%d")
        result.append({"date": day, "title": title, "url": path.removeprefix("docs/"), "commit": sha[:8]})
# Keep previously curated entries, including historical entries without commit IDs.
entries = result + existing
unique = []
keys = set()
for item in entries:
    key = (item.get("commit"), item["url"], item["title"]) if item.get("commit") else (item["date"], item["url"], item["title"])
    if key not in keys:
        keys.add(key)
        unique.append(item)
unique.sort(key=lambda e: e["date"], reverse=True)
updated = source[:match.start(1)] + json.dumps(unique, ensure_ascii=False, separators=(",", ":")) + source[match.end(1):]
if updated != source:
    FILE.write_text(updated, encoding="utf-8")
    print(f"Updated {len(unique)} changelog entries")
else:
    print("No changelog changes")
