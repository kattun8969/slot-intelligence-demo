"""Composable research-only pipeline for the independent EV modules.

No source scraping, no website writes, and no invented episodes. Dependencies
are injected so this PR can be reviewed independently of PRs #32-#34.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Sequence


class PipelineError(ValueError):
    pass


@dataclass(frozen=True)
class PipelineResult:
    source_count: int
    normalized_count: int
    audit_group_count: int
    blocked_group_count: int
    rejected_observations: tuple[dict[str, Any], ...]
    audit_groups: tuple[dict[str, Any], ...]
    estimate_candidates: tuple[dict[str, Any], ...]
    publication_status: str = "research_only"

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": 1, "kind": "ev-research-pipeline",
            "source_count": self.source_count,
            "normalized_count": self.normalized_count,
            "audit_group_count": self.audit_group_count,
            "blocked_group_count": self.blocked_group_count,
            "rejected_observations": list(self.rejected_observations),
            "audit_groups": list(self.audit_groups),
            "estimate_candidates": list(self.estimate_candidates),
            "publication_status": self.publication_status,
            "notice": "Research only. No public EV table is generated from unverified hall events.",
        }


def run_pipeline(
    raw_observations: Sequence[dict[str, Any]],
    *,
    normalize: Callable[[dict[str, Any]], dict[str, Any]],
    audit: Callable[[list[dict[str, Any]]], dict[str, Any]],
    episodes: Sequence[dict[str, Any]] = (),
    summarize: Callable[[list[dict[str, Any]]], list[dict[str, Any]]] | None = None,
) -> PipelineResult:
    """Audit observations; accept only separately documented complete episodes.

    Normalization output contract:
      review_status, source_id, venue_id, machine_id, model_revision,
      observed_date, original_counter_label, original_event_label,
      original_value, counter_type, counter_origin, event_type,
      evidence_url, plus machine_number, observed_at, event_order.
    Never auto-construct episodes from observation events.
    """
    accepted = []
    rejected = []
    for i, source in enumerate(raw_observations):
        try:
            row = normalize(source)
            if not isinstance(row, dict):
                raise PipelineError("normalizer must return dict")
            if row.get("review_status") != "verified":
                rejected.append({"row": i, "reason": "unverified mapping"})
                continue
            required = ("source_id", "venue_id", "machine_id", "model_revision",
                        "machine_number", "observed_at", "event_order",
                        "event_type", "counter_type", "original_value",
                        "counter_origin", "evidence_url")
            missing = [k for k in required if k not in row]
            if missing:
                rejected.append({"row": i, "reason": "missing fields: " + ", ".join(missing)})
                continue
            accepted.append({
                "source_id": row["source_id"], "venue_id": row["venue_id"],
                "machine_id": row["machine_id"], "model_revision": row["model_revision"],
                "machine_number": row["machine_number"],
                "observed_at": row["observed_at"], "event_order": row["event_order"],
                "event_type": row["event_type"], "counter_type": row["counter_type"],
                "counter_value": row["original_value"],
                "counter_origin": row["counter_origin"],
                "review_status": "verified", "source_url": row["evidence_url"],
            })
        except (ValueError, TypeError, KeyError) as exc:
            rejected.append({"row": i, "reason": str(exc)})
    audited = audit(accepted) if accepted else {"group_count": 0, "groups": []}
    if not isinstance(audited, dict) or not isinstance(audited.get("groups"), list):
        raise PipelineError("invalid audit response")
    groups = audited["groups"]
    # Even when audit groups contain no flags, hall events alone are NOT
    # complete player episodes and must never flow to the EV estimator.
    estimates = []
    if episodes:
        if summarize is None:
            raise PipelineError("complete episode summarizer is required")
        estimates = summarize(list(episodes))
        if not isinstance(estimates, list):
            raise PipelineError("invalid summary response")
        for item in estimates:
            if not isinstance(item, dict) or item.get("publication_status") != "research_only":
                raise PipelineError("estimator must return research_only results")
    return PipelineResult(
        source_count=len(raw_observations), normalized_count=len(accepted),
        audit_group_count=len(groups),
        blocked_group_count=sum(not bool(g.get("ev_ready")) for g in groups),
        rejected_observations=tuple(rejected), audit_groups=tuple(groups),
        estimate_candidates=tuple(estimates),
    )
