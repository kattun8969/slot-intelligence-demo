"""Research-only CSV -> verified counter mapping -> event audit bridge.

All dependencies injected to keep the feature independent of unmerged EV PRs.
No hall events become complete player episodes or public EV estimates.
"""
from __future__ import annotations

from typing import Any, Callable

class BridgeError(ValueError):
    pass

def process_csv_to_audit(
    csv_text: str, *, rules: list[dict[str, Any]],
    intake: Callable[[str], dict[str, Any]],
    normalize: Callable[[dict[str, Any], list[dict[str, Any]]], Any],
    to_audit: Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]],
    audit: Callable[[list[dict[str, Any]]], dict[str, Any]],
) -> dict[str, Any]:
    imported = intake(csv_text)
    if not isinstance(imported, dict) or not isinstance(imported.get("accepted"), list):
        raise BridgeError("invalid CSV intake contract")
    accepted = []
    quarantine = list(imported.get("quarantine", []))
    for i, raw in enumerate(imported["accepted"]):
        # Quarantine each observation independently; never guess rule mappings.
        try:
            normalized = normalize(raw, rules)
            if hasattr(normalized, "to_dict"):
                normalized = normalized.to_dict()
            if not isinstance(normalized, dict):
                raise BridgeError("normalizer must return dict")
            audit_row = to_audit(raw, normalized)
            if not isinstance(audit_row, dict):
                raise BridgeError("audit adapter must return dict")
            accepted.append(audit_row)
        except (ValueError, TypeError, KeyError) as exc:
            quarantine.append({
                "source_record_id": raw.get("source_record_id"),
                "reason": "normalization_or_adapter:" + str(exc),
            })
    audited = audit(accepted) if accepted else {"group_count": 0, "groups": []}
    if not isinstance(audited, dict) or not isinstance(audited.get("groups"), list):
        raise BridgeError("invalid audit contract")
    groups = audited["groups"]
    if any(g.get("ev_ready") is not False for g in groups):
        raise BridgeError("hall event audit must explicitly mark ev_ready false")
    return {
        "schema": 1, "kind": "hall-csv-audit-bridge",
        "csv_accepted_count": imported.get("accepted_count"),
        "audit_event_count": len(accepted),
        "audit_group_count": len(groups),
        "quarantined_count": len(quarantine),
        "quarantine": quarantine,
        "audit_groups": groups,
        "estimate_candidates": [],
        "publication_status": "research_only",
        "notice": "Observed hall event streams are not completed player episodes.",
    }
