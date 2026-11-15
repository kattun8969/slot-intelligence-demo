"""Offline, read-only authorized CSV intake -> verified mapping -> pinned audit CLI.

Never contacts a data provider, publishes an EV, or modifies the input files.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any
from scripts.ev_hall_csv_import import import_observations_csv
from scripts.ev_counter_normalizer import normalize, load_rules
from scripts.ev_contract_adapters import observation_to_audit
from scripts.ev_episode_audit import audit_event_stream
from scripts.ev_counter_rule_history import pin_observation
from scripts.ev_csv_audit_bridge import process_csv_to_audit

class AuditCLIError(ValueError):
    pass

def inspect_csv(text: str, rules: list[dict[str, Any]]) -> dict[str, Any]:
    result = process_csv_to_audit(
        text, rules=rules, intake=import_observations_csv,
        normalize=normalize, to_audit=observation_to_audit,
        audit=audit_event_stream, pin_rule=pin_observation)
    return {
        "schema": 1, "kind": "offline-ev-csv-audit-report",
        "csv_accepted_count": result["csv_accepted_count"],
        "audit_event_count": result["audit_event_count"],
        "audit_group_count": result["audit_group_count"],
        "quarantined_count": result["quarantined_count"],
        "quarantine": result["quarantine"],
        "pinned_rule_snapshots": result["pinned_rule_snapshots"],
        "audit_groups": result["audit_groups"],
        "estimate_candidates": [],
        "publication_status": "research_only",
        "notice": "Only authorized input. No real EV or completed episodes inferred.",
    }

def main() -> int:
    parser = argparse.ArgumentParser(description="Audit user-authorized hall CSV offline; JSON to stdout")
    parser.add_argument("csv", type=Path, help="User-provided authorized CSV path")
    parser.add_argument("--rules", type=Path, default=Path("data/ev/counter-rules.json"))
    parser.add_argument("--summary-only", action="store_true", help="Do not print source identifiers or event details")
    args = parser.parse_args()
    rules = load_rules(args.rules)
    report = inspect_csv(args.csv.read_text(encoding="utf-8-sig"), rules)
    if args.summary_only:
        report = {k: report[k] for k in (
            "schema", "kind", "csv_accepted_count", "audit_event_count",
            "audit_group_count", "quarantined_count",
            "estimate_candidates", "publication_status", "notice")}
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
