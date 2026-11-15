"""Strict research-only observed-episode EV summary with per-episode counter origin.

Unlike the legacy exploratory summary, this refuses inferred/simulated states,
unverified counter origins and missing source evidence. No publication permission.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date
from math import sqrt
from statistics import mean, stdev
from urllib.parse import urlparse
from typing import Any

from scripts.ev_engine_core import InvalidEpisode, validate_episode
from scripts.ev_counter_normalizer import ORIGINS
from scripts.ev_counter_rule_history import verify_pinned_snapshot

def _https(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        u = urlparse(value)
        return u.scheme == "https" and bool(u.hostname) and not u.username and not u.password
    except ValueError:
        return False

def validate_observed_episode(row: dict[str, Any]) -> dict[str, Any]:
    e = validate_episode(row)
    if e["state_evidence"] != "observed":
        raise InvalidEpisode("actual observed summary requires observed state evidence")
    origin = row.get("counter_origin")
    if origin not in ORIGINS - {"unknown"}:
        raise InvalidEpisode("verified counter origin required per episode")
    for key in ("source_url", "permission_evidence", "origin_evidence_url"):
        if not _https(row.get(key)):
            raise InvalidEpisode("missing or invalid HTTPS provenance: " + key)
    if row.get("source_permission") == "manual_public_record":
        raise InvalidEpisode("public hall record alone cannot prove player investment and payout")
    if not isinstance(row.get("rule_pin"), dict) or not isinstance(row.get("rule_snapshot"), dict):
        raise InvalidEpisode("immutable rule snapshot and pin required")
    pin = row["rule_pin"]
    snapshot = row["rule_snapshot"]
    if not verify_pinned_snapshot(pin, snapshot):
        raise InvalidEpisode("counter rule fingerprint mismatch")
    if snapshot.get("counter_origin") != origin or snapshot.get("counter_type") != e["counter_type"]:
        raise InvalidEpisode("episode counter origin or type mismatches pinned rule")
    if (pin.get("source_id") != row.get("source_id") or
        snapshot.get("machine_id") != e["machine_id"] or
        snapshot.get("model_revision") != e["model_revision"] or
        snapshot.get("venue_id") != e["venue_id"]):
        raise InvalidEpisode("episode provenance identity mismatch")
    try:
        day = date.fromisoformat(e["date"])
    except (TypeError, ValueError) as exc:
        raise InvalidEpisode("invalid episode date") from exc
    if day.isoformat() != e["date"] or not (snapshot["valid_from"] <= e["date"] <= snapshot["valid_until"]):
        raise InvalidEpisode("rule not effective on episode date")
    if not isinstance(row.get("source_id"), str) or not row["source_id"].strip():
        raise InvalidEpisode("source ID required")
    return e

def summarize_observed_episodes(rows: list[dict[str, Any]], *, min_samples: int = 30) -> list[dict[str, Any]]:
    if isinstance(min_samples, bool) or not isinstance(min_samples, int) or min_samples < 2:
        raise ValueError("min_samples must be integer >= 2")
    groups: dict[tuple, list[float]] = defaultdict(list)
    seen = set()
    for row in rows:
        e = validate_observed_episode(row)
        identity = (row["source_id"], e["venue_id"], e["date"], e["episode_id"])
        if identity in seen:
            raise InvalidEpisode("duplicate observed episode identity")
        seen.add(identity)
        key = (e["machine_id"], e["model_revision"], e["counter_type"],
               row["counter_origin"], e["counter_value"], e["state"],
               e["exchange_basis"], e["play_end_condition"])
        groups[key].append(e["net_yen"])
    output = []
    for key, values in sorted(groups.items()):
        n = len(values)
        avg = mean(values)
        se = stdev(values) / sqrt(n) if n > 1 else None
        output.append({
            "machine_id": key[0], "model_revision": key[1],
            "counter_type": key[2], "counter_origin": key[3],
            "counter_value": key[4], "state": key[5],
            "exchange_basis": key[6], "play_end_condition": key[7],
            "sample_size": n, "mean_net_yen": round(avg, 2),
            "standard_error_yen": round(se, 2) if se is not None else None,
            "ci95_low_yen": round(avg - 1.96 * se, 2) if se is not None else None,
            "ci95_high_yen": round(avg + 1.96 * se, 2) if se is not None else None,
            "sample_threshold_met": n >= min_samples,
            "provenance": "observed_episodes",
            "publication_status": "research_only",
            "warning": "Verified episodes are not randomized; selection bias and setting distribution remain unverified. Not strategy EV.",
        })
    return output
