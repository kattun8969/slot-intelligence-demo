"""Conservative event-stream audit for future EV episode reconstruction.

This stage detects counter resets, missing chronology, event ambiguity, and
right-censoring. It intentionally does NOT infer play starts, investment,
payouts, hidden AT/CZ state, or profitable entry points from hall histories.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

KNOWN_EVENTS = {"at_start", "at_end", "cz_start", "cz_end", "bonus",
                "single_hit_claim", "runthrough_claim", "reset_claim",
                "display_difference", "unknown"}
COUNTERS = {"at_games", "cz_games", "bonus_games", "cycle_number",
            "cycle_games", "screen_points", "daily_difference_medals",
            "section_difference_medals", "unknown"}
RESET_EVIDENCE = {"verified_reset", "verified_power_on"}
AMBIGUOUS = {"single_hit_claim", "runthrough_claim", "reset_claim", "unknown"}

class EventStreamError(ValueError):
    pass

def _validate(record: dict[str, Any]) -> dict[str, Any]:
    fields = ("source_id", "venue_id", "machine_id", "model_revision",
              "machine_number", "observed_at", "event_order", "event_type",
              "counter_type", "counter_value", "counter_origin",
              "review_status", "source_url")
    missing = [k for k in fields if k not in record]
    if missing:
        raise EventStreamError("missing fields: " + ", ".join(missing))
    try:
        timestamp = datetime.fromisoformat(record["observed_at"])
    except (TypeError, ValueError) as exc:
        raise EventStreamError("invalid observed_at") from exc
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise EventStreamError("observed_at must have timezone")
    if isinstance(record["event_order"], bool) or not isinstance(record["event_order"], int) or record["event_order"] < 0:
        raise EventStreamError("event_order must be nonnegative integer")
    if isinstance(record["counter_value"], bool) or not isinstance(record["counter_value"], int):
        raise EventStreamError("counter_value must be integer")
    if record["event_type"] not in KNOWN_EVENTS or record["counter_type"] not in COUNTERS:
        raise EventStreamError("unknown event or counter")
    if record["counter_value"] < 0 and record["counter_type"] not in {"daily_difference_medals", "section_difference_medals"}:
        raise EventStreamError("negative value requires signed-difference counter")
    if record["review_status"] not in {"verified", "unmapped", "ambiguous"}:
        raise EventStreamError("invalid review status")
    if not isinstance(record["source_url"], str) or not record["source_url"].startswith("https://"):
        raise EventStreamError("missing source URL")
    for key in ("source_id", "venue_id", "machine_id", "model_revision", "machine_number", "counter_origin"):
        if not isinstance(record[key], str) or not record[key]:
            raise EventStreamError("missing " + key)
    return dict(record)

def audit_event_stream(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Return isolated, ordered audit groups with explicit blocking reasons."""
    groups = defaultdict(list)
    for row in rows:
        r = _validate(row)
        key = (r["source_id"], r["venue_id"], r["machine_id"],
               r["model_revision"], r["machine_number"])
        groups[key].append(r)
    out = []
    for key, events in sorted(groups.items()):
        # Time ordering is observed evidence; do not silently fix unsorted input.
        flags = set()
        times = [datetime.fromisoformat(x["observed_at"]) for x in events]
        if times != sorted(times):
            flags.add("out_of_order_input")
        if len({(x["observed_at"], x["event_order"]) for x in events}) != len(events):
            flags.add("duplicate_event_identity")
        ordered = sorted(events, key=lambda x: (datetime.fromisoformat(x["observed_at"]), x["event_order"]))
        for a, b in zip(ordered, ordered[1:]):
            if a["event_order"] >= b["event_order"]:
                flags.add("non_monotonic_event_order")
            if a["counter_type"] == b["counter_type"] and a["counter_type"] not in {"daily_difference_medals", "section_difference_medals"} and a["counter_origin"] == b["counter_origin"] and b["counter_value"] < a["counter_value"]:
                flags.add("counter_decreased_without_verified_boundary")
            if datetime.fromisoformat(b["observed_at"]) - datetime.fromisoformat(a["observed_at"]) > __import__("datetime").timedelta(hours=24):
                flags.add("long_observation_gap")
        if any(x["review_status"] != "verified" for x in ordered):
            flags.add("unverified_counter_mapping")
        if any(x["event_type"] in AMBIGUOUS for x in ordered):
            flags.add("ambiguous_outcome_label")
        if any(x["counter_type"] == "unknown" or x["counter_origin"] == "unknown" for x in ordered):
            flags.add("unknown_counter_origin")
        if any(x["event_type"] in RESET_EVIDENCE for x in ordered):
            flags.add("unexpected_reset_marker")
        if not ordered or ordered[0]["event_type"] not in {"at_start", "cz_start"}:
            flags.add("left_censored_entry")
        if not ordered or ordered[-1]["event_type"] not in {"at_end", "cz_end"}:
            flags.add("right_censored_outcome")
        if len({x["observed_at"][:10] for x in ordered}) > 1:
            flags.add("cross_day_sequence_requires_venue_business_day_rules")
        out.append({
            "source_id": key[0], "venue_id": key[1],
            "machine_id": key[2], "model_revision": key[3],
            "machine_number": key[4], "event_count": len(ordered),
            "start_at": ordered[0]["observed_at"], "end_at": ordered[-1]["observed_at"],
            "events": ordered, "flags": sorted(flags),
            "ev_ready": False,
            "status": "review_required",
            "reason": "A public event stream alone cannot identify play-entry selection, actual stake/payout, settings, or hidden machine state."
        })
    return {"schema": 1, "kind": "event-stream-audit",
            "group_count": len(out), "groups": out,
            "notice": "This is an observation quality audit, not a machine EV estimate."}
