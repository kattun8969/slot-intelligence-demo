"""Versioned, conservative source-specific counter normalization.

This module does not scrape sites or infer hidden game states. A provider's
published counter definition must be manually reviewed before activation.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date
from typing import Any
import json
from pathlib import Path

CANONICAL_COUNTERS = {
    "at_games", "cz_games", "bonus_games", "cycle_number",
    "cycle_games", "screen_points", "daily_difference_medals",
    "section_difference_medals", "unknown"
}
EVENTS = {"at_start", "at_end", "cz_start", "cz_end", "bonus",
          "single_hit_claim", "runthrough_claim", "reset_claim",
          "display_difference", "unknown"}
ORIGINS = {"last_at_end", "last_cz_end", "last_bonus_end", "daily_open",
           "screen_cycle_start", "section_start", "unknown"}

class RuleError(ValueError):
    pass

@dataclass(frozen=True)
class NormalizedObservation:
    source_id: str
    venue_id: str
    machine_id: str
    model_revision: str
    observed_date: str
    original_counter_label: str
    original_event_label: str
    original_value: int
    counter_type: str
    counter_origin: str
    event_type: str
    state: str
    rule_id: str | None
    rule_version: int | None
    review_status: str
    evidence_url: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

def validate_rule(rule: dict[str, Any]) -> dict[str, Any]:
    fields = ("id", "version", "source_id", "venue_id", "machine_id",
              "model_revision", "valid_from", "valid_until", "counter_label",
              "event_label", "counter_type", "counter_origin", "event_type",
              "evidence_url", "review_status")
    if any(k not in rule for k in fields):
        raise RuleError("missing rule fields")
    if rule["counter_type"] not in CANONICAL_COUNTERS:
        raise RuleError("invalid counter")
    if rule["event_type"] not in EVENTS or rule["counter_origin"] not in ORIGINS:
        raise RuleError("invalid event or origin")
    if rule["review_status"] not in {"verified", "pending", "rejected"}:
        raise RuleError("invalid review status")
    if not isinstance(rule["version"], int) or isinstance(rule["version"], bool) or rule["version"] < 1:
        raise RuleError("invalid version")
    for key in ("id", "source_id", "venue_id", "machine_id",
                "model_revision", "counter_label", "event_label"):
        if not isinstance(rule[key], str) or not rule[key].strip():
            raise RuleError("empty " + key)
    try:
        start = date.fromisoformat(rule["valid_from"])
        end = date.fromisoformat(rule["valid_until"])
    except (ValueError, TypeError) as exc:
        raise RuleError("invalid date range") from exc
    if start > end:
        raise RuleError("invalid date order")
    if rule["review_status"] == "verified":
        if not str(rule["evidence_url"]).startswith("https://"):
            raise RuleError("verified rules require HTTPS evidence")
        if rule["counter_type"] == "unknown" or rule["counter_origin"] == "unknown":
            raise RuleError("verified rules cannot have unknown counter semantics")
    return rule

def normalize(raw: dict[str, Any], rules: list[dict[str, Any]]) -> NormalizedObservation:
    required = ("source_id", "venue_id", "machine_id", "model_revision",
                "observed_date", "counter_label", "event_label", "counter_value",
                "evidence_url")
    if any(k not in raw for k in required):
        raise RuleError("missing raw observation fields")
    try:
        day = date.fromisoformat(raw["observed_date"])
    except (ValueError, TypeError) as exc:
        raise RuleError("invalid observed date") from exc
    v = raw["counter_value"]
    if isinstance(v, bool) or not isinstance(v, int) or v < 0:
        raise RuleError("counter must be nonnegative integer")
    candidates = []
    for rule in rules:
        validate_rule(rule)
        if rule["review_status"] != "verified":
            continue
        if all(raw[k] == rule[k] for k in ("source_id", "venue_id", "machine_id",
                                         "model_revision", "counter_label", "event_label")):
            if date.fromisoformat(rule["valid_from"]) <= day <= date.fromisoformat(rule["valid_until"]):
                candidates.append(rule)
    # Ambiguous rules are never selected by guessing a newest version.
    status = "verified" if len(candidates) == 1 else ("ambiguous" if candidates else "unmapped")
    r = candidates[0] if len(candidates) == 1 else None
    return NormalizedObservation(
        source_id=raw["source_id"], venue_id=raw["venue_id"],
        machine_id=raw["machine_id"], model_revision=raw["model_revision"],
        observed_date=raw["observed_date"], original_counter_label=raw["counter_label"],
        original_event_label=raw["event_label"], original_value=v,
        counter_type=r["counter_type"] if r else "unknown",
        counter_origin=r["counter_origin"] if r else "unknown",
        event_type=r["event_type"] if r else "unknown",
        state="unverified", rule_id=r["id"] if r else None,
        rule_version=r["version"] if r else None, review_status=status,
        evidence_url=raw["evidence_url"],
    )

def load_rules(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != 1 or not isinstance(data.get("rules"), list):
        raise RuleError("invalid rule registry")
    for rule in data["rules"]:
        validate_rule(rule)
    return data["rules"]
