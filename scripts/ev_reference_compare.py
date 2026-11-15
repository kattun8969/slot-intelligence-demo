"""Condition-matched EV reference comparison. Research-only; no interpolation.

Published reference values and independent observed estimates must share
counter origin, state, model revision, exchange, stop rule and starting point.
"""
from __future__ import annotations

from collections import defaultdict
from math import isfinite
from typing import Any

REQUIRED = (
    "machine_id", "model_revision", "counter_type", "counter_origin",
    "counter_value", "state", "exchange_basis", "play_end_condition"
)
PROVENANCE = {"published_reference", "observed_episodes", "inferred", "simulated"}
class ComparisonError(ValueError):
    pass

def _check(row: dict[str, Any], *, expected: str) -> tuple:
    missing = [key for key in REQUIRED if key not in row]
    if missing:
        raise ComparisonError("missing matching conditions: " + ", ".join(missing))
    if row.get("provenance") != expected:
        raise ComparisonError("provenance mismatch: expected " + expected)
    for key in REQUIRED:
        if isinstance(row[key], bool) or row[key] is None or (isinstance(row[key], str) and not row[key].strip()):
            raise ComparisonError("invalid condition: " + key)
    value = row["counter_value"]
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ComparisonError("counter_value must be nonnegative integer")
    amount_key = "ev_yen" if expected == "published_reference" else "mean_net_yen"
    amount = row.get(amount_key)
    if isinstance(amount, bool) or not isinstance(amount, (int, float)) or not isfinite(amount):
        raise ComparisonError("invalid amount: " + amount_key)
    if expected == "published_reference":
        if not str(row.get("source_url", "")).startswith("https://"):
            raise ComparisonError("published reference needs source URL")
        if not row.get("checked_at"):
            raise ComparisonError("published reference needs checked_at")
    else:
        n = row.get("sample_size")
        if isinstance(n, bool) or not isinstance(n, int) or n < 1:
            raise ComparisonError("observed estimate needs positive sample size")
        if row.get("publication_status") != "research_only":
            raise ComparisonError("observed estimates must remain research_only")
    return tuple(row[key] for key in REQUIRED)

def compare_exact(
    references: list[dict[str, Any]], estimates: list[dict[str, Any]],
    *, min_samples: int = 30
) -> dict[str, Any]:
    if isinstance(min_samples, bool) or not isinstance(min_samples, int) or min_samples < 2:
        raise ComparisonError("min_samples must be integer >= 2")
    ref_index = defaultdict(list)
    for row in references:
        ref_index[_check(row, expected="published_reference")].append(row)
    comparisons = []
    unmatched = []
    for estimate in estimates:
        key = _check(estimate, expected="observed_episodes")
        candidates = ref_index.get(key, [])
        if len(candidates) != 1:
            unmatched.append({
                "conditions": dict(zip(REQUIRED, key)),
                "reason": "no_exact_reference" if not candidates else "ambiguous_reference",
                "reference_count": len(candidates),
            })
            continue
        reference = candidates[0]
        difference = round(estimate["mean_net_yen"] - reference["ev_yen"], 2)
        comparisons.append({
            "conditions": dict(zip(REQUIRED, key)),
            "published_ev_yen": reference["ev_yen"],
            "observed_mean_net_yen": estimate["mean_net_yen"],
            "difference_yen": difference,
            "absolute_difference_yen": abs(difference),
            "sample_size": estimate["sample_size"],
            "sample_threshold_met": estimate["sample_size"] >= min_samples,
            "source_url": reference["source_url"],
            "reference_checked_at": reference["checked_at"],
            "comparison_status": "research_only",
            "limitations": "Observed player episodes may have selection bias; matching conditions does not prove an unbiased strategy EV.",
        })
    return {
        "schema": 1, "kind": "ev-exact-condition-comparison",
        "comparison_count": len(comparisons), "unmatched_count": len(unmatched),
        "comparisons": comparisons, "unmatched": unmatched,
        "publication_status": "research_only",
        "interpolation_used": False,
    }
