"""Fail-closed rule history and pinned mapping provenance for EV research.

An observation must pin the exact rule ID/version/evidence used at analysis time.
This module does not fetch source material or change published EV.
"""
from __future__ import annotations
from datetime import date
from hashlib import sha256
import json
from typing import Any

class RuleHistoryError(ValueError):
    pass

KEYS = ("source_id", "venue_id", "machine_id", "model_revision",
        "counter_label", "event_label")
REQUIRED = KEYS + ("id", "version", "valid_from", "valid_until",
                   "counter_type", "counter_origin", "event_type",
                   "evidence_url", "review_status")
ALLOWED_STATUS = {"verified", "pending", "rejected"}

def _date(value: str) -> date:
    if not isinstance(value, str):
        raise RuleHistoryError("invalid_date")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise RuleHistoryError("invalid_date") from exc
    if parsed.isoformat() != value:
        raise RuleHistoryError("noncanonical_date")
    return parsed

def _validate(rule: dict[str, Any]) -> tuple[date, date]:
    if not isinstance(rule, dict) or any(k not in rule for k in REQUIRED):
        raise RuleHistoryError("missing_rule_fields")
    if any(not isinstance(rule[k], str) or not rule[k].strip() for k in KEYS + ("id",)):
        raise RuleHistoryError("invalid_rule_identity")
    if isinstance(rule["version"], bool) or not isinstance(rule["version"], int) or rule["version"] < 1:
        raise RuleHistoryError("invalid_version")
    if rule["review_status"] not in ALLOWED_STATUS:
        raise RuleHistoryError("invalid_review_status")
    if rule["review_status"] == "verified":
        if not isinstance(rule["evidence_url"], str) or not rule["evidence_url"].startswith("https://"):
            raise RuleHistoryError("verified_rule_requires_https_evidence")
        if rule["counter_type"] == "unknown" or rule["counter_origin"] == "unknown":
            raise RuleHistoryError("verified_rule_cannot_be_unknown")
    start, end = _date(rule["valid_from"]), _date(rule["valid_until"])
    if start > end:
        raise RuleHistoryError("invalid_date_range")
    return start, end

def fingerprint(rule: dict[str, Any]) -> str:
    """Hash the entire rule snapshot; stable across key ordering."""
    _validate(rule)
    canonical = json.dumps(rule, sort_keys=True, ensure_ascii=False,
                           separators=(",", ":"), allow_nan=False)
    return sha256(canonical.encode("utf-8")).hexdigest()

def review_registry(rules: list[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(rules, list):
        raise RuleHistoryError("registry_must_be_list")
    identities = set()
    conflicts = []
    for rule in rules:
        _validate(rule)
        identity = (rule["id"], rule["version"])
        if identity in identities:
            raise RuleHistoryError("duplicate_rule_id_version")
        identities.add(identity)
    for i, first in enumerate(rules):
        a_start, a_end = _validate(first)
        if first["review_status"] != "verified":
            continue
        for second in rules[i+1:]:
            b_start, b_end = _validate(second)
            if (second["review_status"] == "verified"
                and all(first[k] == second[k] for k in KEYS)
                and max(a_start, b_start) <= min(a_end, b_end)):
                conflicts.append({
                    "rule_a": [first["id"], first["version"]],
                    "rule_b": [second["id"], second["version"]],
                    "reason": "overlapping_verified_rule_period",
                })
    return {"schema": 1, "rule_count": len(rules),
            "conflicts": conflicts, "ready": not conflicts,
            "publication_status": "research_only"}

def pin_observation(raw: dict[str, Any], normalized: dict[str, Any],
                    rules: list[dict[str, Any]]) -> dict[str, Any]:
    """Attach an immutable rule snapshot hash; reject changed/unreviewed mappings."""
    if not isinstance(raw, dict) or not isinstance(normalized, dict):
        raise RuleHistoryError("invalid_observation")
    if normalized.get("review_status") != "verified":
        raise RuleHistoryError("mapping_not_verified")
    if review_registry(rules)["conflicts"]:
        raise RuleHistoryError("conflicting_registry")
    matches = [r for r in rules if r["id"] == normalized.get("rule_id")
               and r["version"] == normalized.get("rule_version")]
    if len(matches) != 1:
        raise RuleHistoryError("missing_pinned_rule")
    rule = matches[0]
    if rule["review_status"] != "verified":
        raise RuleHistoryError("pinned_rule_not_verified")
    if any(raw.get(k) != rule[k] for k in KEYS):
        raise RuleHistoryError("rule_identity_mismatch")
    day = _date(raw.get("observed_date"))
    if not (_date(rule["valid_from"]) <= day <= _date(rule["valid_until"])):
        raise RuleHistoryError("rule_outside_effective_period")
    for key in ("counter_type", "counter_origin", "event_type"):
        if normalized.get(key) != rule[key]:
            raise RuleHistoryError("normalized_semantics_mismatch")
    if raw.get("counter_value") != normalized.get("original_value"):
        raise RuleHistoryError("normalized_value_mismatch")
    return {
        "source_id": raw["source_id"],
        "source_record_id": raw.get("source_record_id"),
        "observed_date": raw["observed_date"],
        "counter_type": rule["counter_type"],
        "counter_origin": rule["counter_origin"],
        "rule_id": rule["id"], "rule_version": rule["version"],
        "rule_fingerprint_sha256": fingerprint(rule),
        "rule_evidence_url": rule["evidence_url"],
        "publication_status": "research_only",
    }

def verify_pinned_snapshot(pin: dict[str, Any], rule_snapshot: dict[str, Any]) -> bool:
    if (pin.get("rule_id"), pin.get("rule_version")) != (rule_snapshot.get("id"), rule_snapshot.get("version")):
        return False
    try:
        return pin.get("rule_fingerprint_sha256") == fingerprint(rule_snapshot)
    except (RuleHistoryError, TypeError, ValueError):
        return False
