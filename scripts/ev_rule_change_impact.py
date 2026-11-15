"""Review rule registry changes before any historical observation is reprocessed.

A changed or removed rule version is blocked, even if no current overlap exists.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any
from scripts.ev_counter_rule_history import fingerprint, review_registry

def compare_rule_registries(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    def indexed(registry: dict[str, Any]) -> dict[tuple[str, int], dict[str, Any]]:
        if not isinstance(registry, dict) or registry.get("schema") != 1 or not isinstance(registry.get("rules"), list):
            raise ValueError("invalid_registry_schema")
        rules = registry["rules"]
        review_registry(rules)
        return {(r["id"], r["version"]): r for r in rules}
    old, new = indexed(before), indexed(after)
    added = sorted(set(new) - set(old))
    removed = sorted(set(old) - set(new))
    changed = sorted(k for k in old.keys() & new.keys()
                     if fingerprint(old[k]) != fingerprint(new[k]))
    old_report = review_registry(before["rules"])
    new_report = review_registry(after["rules"])
    blockers = []
    for key in removed:
        blockers.append({"rule_id": key[0], "version": key[1], "reason": "historical_rule_removed"})
    for key in changed:
        blockers.append({"rule_id": key[0], "version": key[1], "reason": "immutable_rule_version_modified"})
    if new_report["conflicts"]:
        blockers.append({"reason": "new_registry_contains_overlapping_verified_rules"})
    return {
        "schema": 1, "kind": "ev-rule-change-impact",
        "added": [{"rule_id": k[0], "version": k[1]} for k in added],
        "removed": [{"rule_id": k[0], "version": k[1]} for k in removed],
        "changed": [{"rule_id": k[0], "version": k[1]} for k in changed],
        "previous_conflicts": old_report["conflicts"],
        "current_conflicts": new_report["conflicts"],
        "blockers": blockers,
        "requires_manual_review": bool(added or blockers),
        "historical_reinterpretation_blocked": bool(blockers),
        "safe_to_reprocess_historical_data": not blockers,
        "publication_status": "research_only",
        "notice": "New rules require human source and permission review; this check does not authorize EV publication.",
    }

def main() -> int:
    parser = argparse.ArgumentParser(description="Compare old and new rule registry snapshots")
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    args = parser.parse_args()
    old = json.loads(args.before.read_text(encoding="utf-8"))
    new = json.loads(args.after.read_text(encoding="utf-8"))
    report = compare_rule_registries(old, new)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 2 if report["historical_reinterpretation_blocked"] else 0

if __name__ == "__main__":
    raise SystemExit(main())
