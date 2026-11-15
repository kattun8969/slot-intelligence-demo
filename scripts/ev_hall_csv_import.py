"""Permission-aware, quarantine-first hall observation CSV intake.

Reads user-provided CSV; never fetches/scrapes provider websites.
No raw hall observation is treated as a completed play episode.
"""
from __future__ import annotations

import csv
import io
from datetime import date, datetime
from urllib.parse import urlparse
from typing import Any

FIELDS = (
    "source_id", "venue_id", "machine_id", "model_revision",
    "machine_number", "observed_date", "observed_at", "event_order",
    "counter_label", "event_label", "counter_value", "evidence_url",
    "source_permission", "permission_evidence", "source_record_id",
)
PERMISSIONS = {"user_owned", "permitted_csv", "official_api", "manual_public_record"}
MAX_BYTES = 5_000_000
MAX_ROWS = 20_000

class IntakeError(ValueError):
    pass

def _https(value: str) -> bool:
    try:
        parsed = urlparse(value)
        return parsed.scheme == "https" and bool(parsed.netloc) and not parsed.username and not parsed.password
    except ValueError:
        return False

def _row(raw: dict[str, str]) -> dict[str, Any]:
    for key in FIELDS:
        if not isinstance(raw.get(key), str) or not raw[key].strip():
            raise IntakeError("missing_or_blank:" + key)
    for key in ("evidence_url", "permission_evidence"):
        if not _https(raw[key]):
            raise IntakeError("invalid_https_url:" + key)
    if raw["source_permission"] not in PERMISSIONS:
        raise IntakeError("permission_not_established")
    try:
        day = date.fromisoformat(raw["observed_date"])
        moment = datetime.fromisoformat(raw["observed_at"])
    except (TypeError, ValueError) as exc:
        raise IntakeError("invalid_date_or_timestamp") from exc
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise IntakeError("timestamp_missing_timezone")
    if moment.date() != day:
        raise IntakeError("observation_calendar_date_mismatch")
    try:
        order = int(raw["event_order"])
        value = int(raw["counter_value"])
    except ValueError as exc:
        raise IntakeError("invalid_integer") from exc
    if order < 0 or value < 0 or str(order) != raw["event_order"] or str(value) != raw["counter_value"]:
        raise IntakeError("invalid_nonnegative_integer")
    return {
        **{k: raw[k].strip() for k in FIELDS},
        "event_order": order, "counter_value": value,
    }

def import_observations_csv(text: str, *, max_rows: int = MAX_ROWS) -> dict[str, Any]:
    if not isinstance(text, str):
        raise IntakeError("CSV must be UTF-8 decoded text")
    if len(text.encode("utf-8")) > MAX_BYTES:
        raise IntakeError("CSV exceeds size limit")
    if not isinstance(max_rows, int) or isinstance(max_rows, bool) or not 1 <= max_rows <= MAX_ROWS:
        raise IntakeError("invalid max_rows")
    reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
    if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise IntakeError("missing or duplicate headers")
    missing = [key for key in FIELDS if key not in reader.fieldnames]
    if missing:
        raise IntakeError("missing headers:" + ",".join(missing))
    if None in reader.fieldnames:
        raise IntakeError("invalid empty header")
    accepted = []
    quarantine = []
    seen = set()
    try:
        for i, raw in enumerate(reader, start=2):
            if i - 1 > max_rows:
                raise IntakeError("CSV row limit exceeded")
            try:
                if None in raw or any(value is None for value in raw.values()):
                    raise IntakeError("malformed_column_count")
                row = _row(raw)
                identity = (row["source_id"], row["venue_id"], row["source_record_id"])
                if identity in seen:
                    raise IntakeError("duplicate_source_record")
                seen.add(identity)
                accepted.append(row)
            except IntakeError as exc:
                quarantine.append({"csv_line": i, "reason": str(exc)})
    except csv.Error as exc:
        raise IntakeError("malformed_csv") from exc
    return {
        "schema": 1, "kind": "hall-observation-csv-intake",
        "accepted_count": len(accepted), "quarantined_count": len(quarantine),
        "accepted": accepted, "quarantine": quarantine,
        "publication_status": "research_only",
        "notice": "Permission labels and URLs are claims requiring external review; no EV inferred.",
    }
