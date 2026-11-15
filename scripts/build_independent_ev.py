#!/usr/bin/env python3
"""Build an independent *observed-profit* report from complete opt-in play logs.

This is research infrastructure, NOT a verified EV model. No paid tables are read.
Use only rows with actual start/end and verified net outcome, don't extrapolate.
"""
from __future__ import annotations
import argparse
import csv
import datetime as dt
import json
import math
from collections import defaultdict
from pathlib import Path

FIELDS = (
    "record_id", "machine", "scenario", "start_g", "end_rule",
    "exchange_yen_per_medal", "settings_known", "play_date",
    "complete", "net_yen", "data_source"
)


def validate(row):
    if not all(key in row for key in FIELDS):
        raise ValueError("CSV missing required column")
    if row["complete"] not in ("yes", "no"):
        raise ValueError("complete must be yes/no")
    if not row["record_id"].strip() or not row["machine"].strip() or not row["scenario"].strip():
        raise ValueError("Missing identity or machine/scenario")
    if not row["end_rule"].strip():
        raise ValueError("Missing end rule")
    start = int(row["start_g"])
    exchange = float(row["exchange_yen_per_medal"])
    dt.date.fromisoformat(row["play_date"])
    if start < 0 or start > 3000 or exchange <= 0 or exchange > 100:
        raise ValueError("Invalid start G / exchange")
    if row["complete"] == "yes":
        result = float(row["net_yen"])
        if not math.isfinite(result) or abs(result) > 2_000_000:
            raise ValueError("Invalid net yen")
    else:
        result = None
    return start, exchange, result


def analyze(records, min_count=50):
    groups = defaultdict(list)
    dropped = defaultdict(int)
    ids = set()
    for row in records:
        start, exchange, result = validate(row)
        if row["record_id"] in ids:
            dropped["duplicate_id"] += 1
            continue
        ids.add(row["record_id"])
        if row["complete"] != "yes":
            dropped["right_censored"] += 1
            continue
        # Keep origin, end rule, exchange AND setting information separate.
        key = (row["machine"], row["scenario"], start, row["end_rule"],
               exchange, row["settings_known"])
        groups[key].append(result)
    summaries = []
    for key, values in sorted(groups.items()):
        if len(values) < min_count:
            dropped["insufficient_n"] += len(values)
            continue
        n = len(values)
        avg = sum(values) / n
        var = sum((v - avg) ** 2 for v in values) / (n - 1) if n > 1 else 0
        se = (var / n) ** 0.5
        summaries.append({
            "machine": key[0], "scenario": key[1], "start_g": key[2],
            "end_rule": key[3], "exchange_yen_per_medal": key[4],
            "settings_known": key[5], "n": n, "mean_net_yen": round(avg, 2),
            "approx_95pct_margin_yen": round(1.96 * se, 2),
            "provenance": "owner-collected completed sessions only",
            "verified_expected_value": False,
        })
    return {
        "schema": 1,
        "status": "independent_research_observed_profit_not_validated_EV",
        "min_count_per_exact_condition": min_count,
        "note": "右打ち切り（結果未確認）を0円損失として扱わない。完全記録のみの平均は選択バイアスがあり未来の期待値とは限らない。サンプルが少ない条件は未公開。交換率・設定・終了条件の混在禁止。公開前に生存分析・ホール分布・設定1への補正と検証を要する。",
        "rows": summaries,
        "excluded_counts": dict(dropped),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--min-count", type=int, default=50)
    args = parser.parse_args()
    if args.min_count < 2:
        raise ValueError("min_count must be >= 2")
    with args.input.open(encoding="utf-8-sig", newline="") as f:
        data = analyze(csv.DictReader(f), args.min_count)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print("Independent research rows:", len(data["rows"]))


if __name__ == "__main__":
    main()
