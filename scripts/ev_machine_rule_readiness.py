"""Read-only machine rule readiness report; never invent or activate machine rules.

This is a research readiness index, not a publication gate for site content.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.ev_counter_normalizer import validate_rule
from scripts.ev_counter_rule_history import review_registry

class ReadinessError(ValueError):
    pass

def build_readiness(registry: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(registry, dict) or registry.get("schema") != 1 or not isinstance(registry.get("rules"), list):
        raise ReadinessError("invalid_registry_schema")
    rules = registry["rules"]
    for r in rules:
        validate_rule(r)
    review = review_registry(rules)
    conflicts = review["conflicts"]
    conflicted = {(rid, version) for item in conflicts
                  for rid, version in (item["rule_a"], item["rule_b"])}
    by_machine: dict[tuple[str, str, str, str], list[dict[str, Any]]] = {}
    for r in rules:
        key = (r["source_id"], r["venue_id"], r["machine_id"], r["model_revision"])
        by_machine.setdefault(key, []).append(r)
    machines = []
    for key, items in sorted(by_machine.items()):
        verified = [r for r in items if r["review_status"] == "verified"]
        blocked = [r for r in verified if (r["id"], r["version"]) in conflicted]
        active = [r for r in verified if (r["id"], r["version"]) not in conflicted]
        machines.append({
            "source_id": key[0], "venue_id": key[1],
            "machine_id": key[2], "model_revision": key[3],
            "total_rules": len(items), "verified_rules": len(verified),
            "pending_rules": sum(r["review_status"] == "pending" for r in items),
            "rejected_rules": sum(r["review_status"] == "rejected" for r in items),
            "conflicting_rules": len(blocked),
            "usable_counter_types": sorted({r["counter_type"] for r in active}),
            "mapping_ready": bool(active) and not blocked,
            "observed_episodes_verified": False,
            "ev_publication_ready": False,
        })
    return {
        "schema": 1, "kind": "ev-machine-rule-readiness",
        "registered_machines": len(machines),
        "verified_rule_count": sum(r["review_status"] == "verified" for r in rules),
        "registry_conflicts": conflicts,
        "machines": machines,
        "ev_publication_ready_count": 0,
        "publication_status": "research_only",
        "notice": "Verified counter mapping is not evidence of positive EV, actual episodes, or permission to publish.",
    }

def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect machine counter rule readiness without modifying data")
    parser.add_argument("--registry", type=Path, default=Path("data/ev/counter-rules.json"))
    args = parser.parse_args()
    report = build_readiness(json.loads(args.registry.read_text(encoding="utf-8")))
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
