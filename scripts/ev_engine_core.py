"""Shared experimental EV core. No hall ingestion, no machine-page integration.

Inputs must be verified complete *play episodes* with actual stake/payout.
Never reconstruct cost or hidden state from a hall's daily difference graph.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from math import sqrt
from statistics import mean, stdev
from typing import Any

COUNTERS = {"at_games", "cz_games", "cycle_number", "cycle_games",
            "screen_points", "daily_difference_medals", "section_difference_medals"}
STATES = {"normal", "reset_verified", "after_at", "after_cz_failure",
          "runthrough_verified", "pullback_verified", "upper_at_end_verified"}
EVIDENCE = {"observed", "public_analysis", "inferred", "simulated"}
REQUIRED = {"episode_id", "machine_id", "model_revision", "venue_id", "date",
            "counter_type", "counter_value", "state", "state_evidence",
            "investment_yen", "return_yen", "exchange_basis",
            "play_end_condition", "completed", "source_permission"}

class InvalidEpisode(ValueError):
    pass

def validate_episode(row: dict[str, Any]) -> dict[str, Any]:
    missing = REQUIRED - row.keys()
    if missing:
        raise InvalidEpisode("missing: " + ", ".join(sorted(missing)))
    if row["counter_type"] not in COUNTERS:
        raise InvalidEpisode("unknown counter type")
    if row["state"] not in STATES:
        raise InvalidEpisode("unknown state")
    if row["state_evidence"] not in EVIDENCE:
        raise InvalidEpisode("unknown evidence type")
    if row["state"] in {"reset_verified", "runthrough_verified",
                        "pullback_verified", "upper_at_end_verified"} and row["state_evidence"] != "observed":
        raise InvalidEpisode("claimed verified state requires observed evidence")
    if row["source_permission"] not in {"permitted_csv", "manual_public_record", "official_api", "user_owned"}:
        raise InvalidEpisode("source permission not established")
    if row["completed"] is not True:
        raise InvalidEpisode("incomplete episode; right-censored observations cannot be used as complete")
    for k in ("counter_value", "investment_yen", "return_yen"):
        v = row[k]
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not (float("-inf") < v < float("inf")) or v < 0:
            raise InvalidEpisode("invalid nonnegative number: " + k)
    if row["counter_type"] in {"at_games", "cz_games", "cycle_number", "cycle_games", "screen_points"} and int(row["counter_value"]) != row["counter_value"]:
        raise InvalidEpisode("counter must be integer")
    for k in ("episode_id", "machine_id", "model_revision", "venue_id", "date",
              "exchange_basis", "play_end_condition"):
        if not isinstance(row[k], str) or not row[k].strip():
            raise InvalidEpisode("missing or empty: " + k)
    return dict(row, net_yen=row["return_yen"] - row["investment_yen"])

@dataclass(frozen=True)
class Estimate:
    machine_id: str
    counter_type: str
    state: str
    exchange_basis: str
    play_end_condition: str
    sample_size: int
    mean_net_yen: float
    standard_error_yen: float | None
    ci95_low_yen: float | None
    ci95_high_yen: float | None
    evidence_kind: str = "observed_episodes"
    publication_status: str = "research_only"

    def as_dict(self) -> dict[str, Any]:
        return vars(self).copy()

def summarize_episodes(rows: list[dict[str, Any]], *, min_samples: int = 30) -> list[dict[str, Any]]:
    if min_samples < 2:
        raise ValueError("min_samples must be >= 2")
    groups = defaultdict(list)
    seen = set()
    for row in rows:
        e = validate_episode(row)
        key_id = (e["venue_id"], e["date"], e["episode_id"])
        if key_id in seen:
            raise InvalidEpisode("duplicate episode identity")
        seen.add(key_id)
        key = (e["machine_id"], e["model_revision"], e["counter_type"],
               e["counter_value"], e["state"], e["exchange_basis"],
               e["play_end_condition"], e["state_evidence"])
        groups[key].append(e["net_yen"])
    output = []
    for key, values in sorted(groups.items()):
        machine, revision, counter, value, state, exchange, end, evidence = key
        n = len(values)
        avg = mean(values)
        se = stdev(values) / sqrt(n) if n >= 2 else None
        estimate = {
            "machine_id": machine, "model_revision": revision,
            "counter_type": counter, "counter_value": value, "state": state,
            "exchange_basis": exchange, "play_end_condition": end,
            "state_evidence": evidence, "sample_size": n,
            "mean_net_yen": round(avg, 2),
            "standard_error_yen": round(se, 2) if se is not None else None,
            "ci95_low_yen": round(avg - 1.96 * se, 2) if se is not None else None,
            "ci95_high_yen": round(avg + 1.96 * se, 2) if se is not None else None,
            "publication_status": "research_only",
            "sample_threshold_met": n >= min_samples,
            "warning": "Observed episodes are not randomized. Selection bias, censoring, settings and counter rules must be audited before estimating strategy EV."
        }
        output.append(estimate)
    return output
