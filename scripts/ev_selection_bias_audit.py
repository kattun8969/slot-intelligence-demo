"""Fail-closed sampling and selection-bias audit for observed EV research.

Audits an externally supplied capture manifest; never infers unobserved plays.
A high capture rate is not proof of representative sampling or strategy EV.
"""
from __future__ import annotations

from collections import Counter
from typing import Any
from scripts.ev_observed_episode_provenance import validate_observed_episode
from scripts.ev_engine_core import InvalidEpisode

CAPTURE_METHODS = {"consecutive_all_eligible", "random_sample", "voluntary_submission", "selected_winners", "unknown"}
SETTING_STATUSES = {"verified", "unknown"}

class SamplingAuditError(ValueError):
    pass

def audit_sampling(rows: list[dict[str, Any]], manifest: dict[str, Any], *, min_samples: int = 30) -> dict[str, Any]:
    if isinstance(min_samples, bool) or not isinstance(min_samples, int) or min_samples < 2:
        raise SamplingAuditError("invalid_min_samples")
    if not isinstance(manifest, dict):
        raise SamplingAuditError("invalid_manifest")
    method = manifest.get("capture_method")
    if method not in CAPTURE_METHODS:
        raise SamplingAuditError("invalid_capture_method")
    eligible = manifest.get("eligible_episode_count")
    if isinstance(eligible, bool) or not isinstance(eligible, int) or eligible < 0:
        raise SamplingAuditError("invalid_eligible_episode_count")
    if manifest.get("setting_distribution_status") not in SETTING_STATUSES:
        raise SamplingAuditError("invalid_setting_distribution_status")
    if manifest.get("capture_protocol_predeclared") not in (True, False):
        raise SamplingAuditError("capture_protocol_predeclared_required")
    if manifest.get("all_outcomes_reported") not in (True, False):
        raise SamplingAuditError("all_outcomes_reported_required")
    seen = set()
    observed = []
    for row in rows:
        validated = validate_observed_episode(row)
        identity = (row["source_id"], row["venue_id"], row["date"], row["episode_id"])
        if identity in seen:
            raise InvalidEpisode("duplicate observed episode identity")
        seen.add(identity)
        observed.append(validated)
    count = len(observed)
    if count > eligible:
        raise SamplingAuditError("observed_count_exceeds_eligible_manifest")
    capture_rate = count / eligible if eligible else None
    reasons = []
    if count < min_samples:
        reasons.append("insufficient_sample")
    if eligible == 0:
        reasons.append("empty_eligible_population")
    elif count < eligible:
        reasons.append("unobserved_eligible_episodes")
    if method not in {"consecutive_all_eligible", "random_sample"}:
        reasons.append("selection_prone_capture_method")
    if not manifest["capture_protocol_predeclared"]:
        reasons.append("capture_protocol_not_predeclared")
    if not manifest["all_outcomes_reported"]:
        reasons.append("outcome_reporting_not_complete")
    if manifest["setting_distribution_status"] != "verified":
        reasons.append("setting_distribution_unverified")
    # These gates are necessary but not sufficient for a representative EV.
    return {
        "schema": 1, "kind": "ev-selection-bias-audit",
        "observed_episode_count": count,
        "eligible_episode_count": eligible,
        "capture_rate": round(capture_rate, 6) if capture_rate is not None else None,
        "capture_method": method,
        "setting_distribution_status": manifest["setting_distribution_status"],
        "sampling_warnings": reasons,
        "basic_sampling_checks_passed": not reasons,
        "strategy_ev_verified": False,
        "publication_status": "research_only",
        "notice": "Passing sampling checks does not prove representativeness, settings, profitability or permission to publish.",
    }
