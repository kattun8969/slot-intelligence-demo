"""Explicit compatibility adapters for independently reviewed EV PRs.

No fabricated play episodes or guessed counter origins. Importing this module
does not require the other unmerged PR branches.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

class AdapterError(ValueError):
    pass

def observation_to_audit(raw: dict[str, Any], normalized: dict[str, Any]) -> dict[str, Any]:
    """Bridge PR #33 normalized observations into PR #34 event audits.

    Machine number, event timestamp and sequence MUST come from raw evidence.
    A rule's evidence URL documents counter semantics; it is not a substitute
    for the original observation source URL.
    """
    if normalized.get("review_status") != "verified":
        raise AdapterError("mapping is not verified")
    for key in ("source_id", "venue_id", "machine_id", "model_revision"):
        if not raw.get(key) or raw.get(key) != normalized.get(key):
            raise AdapterError("identity mismatch: " + key)
    for key in ("machine_number", "observed_at", "event_order", "evidence_url"):
        if key not in raw:
            raise AdapterError("missing raw evidence: " + key)
    if not isinstance(raw["machine_number"], str) or not raw["machine_number"].strip():
        raise AdapterError("invalid machine number")
    try:
        ts = datetime.fromisoformat(raw["observed_at"])
    except (TypeError, ValueError) as exc:
        raise AdapterError("invalid timestamp") from exc
    if ts.tzinfo is None or ts.utcoffset() is None:
        raise AdapterError("timestamp must have timezone")
    if ts.date().isoformat() != normalized.get("observed_date"):
        raise AdapterError("observation date mismatch")
    order = raw["event_order"]
    if isinstance(order, bool) or not isinstance(order, int) or order < 0:
        raise AdapterError("invalid event order")
    if not isinstance(raw["evidence_url"], str) or not raw["evidence_url"].startswith("https://"):
        raise AdapterError("observation source URL required")
    if raw.get("counter_value") != normalized.get("original_value"):
        raise AdapterError("counter value mismatch")
    if normalized.get("counter_type") in (None, "unknown") or normalized.get("counter_origin") in (None, "unknown"):
        raise AdapterError("counter semantics unverified")
    return {
        "source_id": raw["source_id"], "venue_id": raw["venue_id"],
        "machine_id": raw["machine_id"], "model_revision": raw["model_revision"],
        "machine_number": raw["machine_number"], "observed_at": raw["observed_at"],
        "event_order": order, "event_type": normalized["event_type"],
        "counter_type": normalized["counter_type"],
        "counter_value": normalized["original_value"],
        "counter_origin": normalized["counter_origin"],
        "review_status": "verified", "source_url": raw["evidence_url"],
    }

def estimate_to_comparison(
    estimate: dict[str, Any], *, counter_origin: str,
    origin_evidence_url: str,
) -> dict[str, Any]:
    """Bridge PR #32 estimates to PR #39 without guessing missing origin.

    The provenance of the observed *state* must be actual observation;
    otherwise a research-only inferred state cannot be mislabeled observed.
    """
    if estimate.get("publication_status") != "research_only":
        raise AdapterError("estimate not research-only")
    if estimate.get("state_evidence") != "observed":
        raise AdapterError("estimate state evidence not observed")
    if not counter_origin or counter_origin == "unknown":
        raise AdapterError("counter origin must be explicitly supplied")
    if not isinstance(origin_evidence_url, str) or not origin_evidence_url.startswith("https://"):
        raise AdapterError("counter origin needs source evidence")
    required = ("machine_id", "model_revision", "counter_type", "counter_value",
                "state", "exchange_basis", "play_end_condition", "sample_size",
                "mean_net_yen")
    missing = [k for k in required if k not in estimate]
    if missing:
        raise AdapterError("missing estimate fields: " + ", ".join(missing))
    return {
        **{k: estimate[k] for k in required},
        "counter_origin": counter_origin, "origin_evidence_url": origin_evidence_url,
        "provenance": "observed_episodes", "publication_status": "research_only",
    }
