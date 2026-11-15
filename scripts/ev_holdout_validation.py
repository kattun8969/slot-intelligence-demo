"""Time-based out-of-sample EV validation for independently observed episodes.

Only complete, actual-stake episodes are accepted. Do not use public hall
event counts as independent samples. This module never publishes a pick.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date
from math import isfinite, sqrt
from statistics import mean, stdev
from typing import Any

KEYS = ("machine_id", "model_revision", "counter_type", "counter_origin",
        "counter_value", "state", "exchange_basis", "play_end_condition")

class ValidationError(ValueError):
    pass

def _episode(row: dict[str, Any]) -> tuple[tuple, date, float, str]:
    needed = (*KEYS, "venue_id", "episode_id", "date", "investment_yen",
              "return_yen", "completed", "source_permission")
    missing = [k for k in needed if k not in row]
    if missing:
        raise ValidationError("missing: " + ", ".join(missing))
    if row["completed"] is not True:
        raise ValidationError("censored episode")
    if row["source_permission"] not in {"permitted_csv", "manual_public_record", "official_api", "user_owned"}:
        raise ValidationError("source not authorized")
    for k in (*KEYS, "venue_id", "episode_id"):
        if row[k] is None or isinstance(row[k], bool) or (isinstance(row[k], str) and not row[k].strip()):
            raise ValidationError("invalid " + k)
    if isinstance(row["counter_value"], bool) or not isinstance(row["counter_value"], int) or row["counter_value"] < 0:
        raise ValidationError("invalid counter")
    try:
        day = date.fromisoformat(row["date"])
    except (TypeError, ValueError) as exc:
        raise ValidationError("invalid date") from exc
    for k in ("investment_yen", "return_yen"):
        v = row[k]
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not isfinite(v) or v < 0:
            raise ValidationError("invalid cash flow: " + k)
    return tuple(row[k] for k in KEYS), day, row["return_yen"] - row["investment_yen"], row["venue_id"]

def validate_holdout(
    episodes: list[dict[str, Any]], *, split_date: str,
    min_train: int = 30, min_test: int = 30
) -> dict[str, Any]:
    """Train strictly before split_date, test on/after split_date.

    Reports means, holdout bias and sample uncertainty; never selects a
    favorable threshold based on the test data.
    """
    try:
        boundary = date.fromisoformat(split_date)
    except (TypeError, ValueError) as exc:
        raise ValidationError("invalid split date") from exc
    if any(isinstance(v, bool) or not isinstance(v, int) or v < 2 for v in (min_train, min_test)):
        raise ValidationError("minimum samples must be integers >= 2")
    seen = set()
    groups = defaultdict(lambda: {"train": [], "test": [], "venues_train": set(), "venues_test": set()})
    for row in episodes:
        key, day, net, venue = _episode(row)
        identity = (venue, row["date"], row["episode_id"])
        if identity in seen:
            raise ValidationError("duplicate episode")
        seen.add(identity)
        part = "train" if day < boundary else "test"
        groups[key][part].append(net)
        groups[key]["venues_" + part].add(venue)
    reports = []
    for key, group in sorted(groups.items()):
        train, test = group["train"], group["test"]
        n_train, n_test = len(train), len(test)
        avg_train = mean(train) if train else None
        avg_test = mean(test) if test else None
        se_test = stdev(test) / sqrt(n_test) if n_test >= 2 else None
        eligible = n_train >= min_train and n_test >= min_test
        reports.append({
            "conditions": dict(zip(KEYS, key)),
            "train_n": n_train, "test_n": n_test,
            "train_venue_n": len(group["venues_train"]),
            "test_venue_n": len(group["venues_test"]),
            "train_mean_yen": round(avg_train, 2) if avg_train is not None else None,
            "test_mean_yen": round(avg_test, 2) if avg_test is not None else None,
            "holdout_difference_yen": round(avg_test - avg_train, 2) if avg_train is not None and avg_test is not None else None,
            "test_standard_error_yen": round(se_test, 2) if se_test is not None else None,
            "minimum_samples_met": eligible,
            "validation_status": "research_only" if eligible else "insufficient_samples",
            "warning": "Temporal holdout does not correct selection bias, nonrandom settings, right censoring, or correlated episodes.",
        })
    return {"schema": 1, "kind": "ev-temporal-holdout", "split_date": split_date,
            "groups": reports, "group_count": len(reports),
            "publication_status": "research_only"}
