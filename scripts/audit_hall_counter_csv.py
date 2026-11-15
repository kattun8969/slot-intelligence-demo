#!/usr/bin/env python3
"""Validate permitted public hall exports; do not infer hidden AT, CZ or settings.

Use a CSV downloaded under the hall's terms / explicit permission.
This stage produces REVIEW-ONLY normalized rows, not EV estimates.
"""
from __future__ import annotations
import argparse
import csv
import datetime as dt
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REQUIRED=("venue_id","machine_model","model_revision","data_date","machine_number",
          "counter_label","counter_value","counter_unit","event_label",
          "event_order","source_url","collection_method","observation_confidence",
          "rules_verified")
ALLOWED_UNITS={"G","pt","cycle","times","medals","unknown"}
ALLOWED_CONFIDENCE={"observed","inferred","unknown"}
ALLOWED_METHOD={"permitted_csv","manual_public_record","official_api"}
# Unknown labels MUST stay unknown; transformations require a venue + machine-specific rule.
ALIASES={
 "big":"bonus","reg":"bonus","rb":"bonus","bb":"bonus",
 "bonus":"bonus","ボーナス":"bonus","AT":"AT","ST":"ST","CZ":"CZ",
 "大当り":"hit_unspecified","初当り":"hit_unspecified",
 "駆け抜け":"claimed_run_through","単発":"claimed_single",
 "差枚":"difference_display","終了":"end_unspecified",
 "リセット":"claimed_reset"
}
LABELS={key.casefold():value for key,value in ALIASES.items()}
MAX_ROWS=20000
DANGEROUS_FORMULA=re.compile(r"^[=+\-@]")


def parse_csv(path:Path)->tuple[list[dict],list[dict]]:
    accepted=[];held=[]
    with path.open("r",encoding="utf-8-sig",newline="") as fh:
        reader=csv.DictReader(fh)
        if not reader.fieldnames or not set(REQUIRED).issubset(reader.fieldnames):
            missing=set(REQUIRED)-set(reader.fieldnames or [])
            raise ValueError("CSV required columns missing: "+", ".join(sorted(missing)))
        for i,row in enumerate(reader,2):
            if i>MAX_ROWS+1:raise ValueError("CSV row limit exceeded")
            reasons=[]
            for field in REQUIRED:
                if not str(row.get(field) or "").strip():reasons.append("empty "+field)
            try:
                day=dt.date.fromisoformat(row["data_date"])
                if day>dt.date.today():reasons.append("future data_date")
            except(ValueError,TypeError):
                reasons.append("invalid data_date")
            try:
                number=float(row.get("counter_value",""))
                if not number.is_integer() or number<0:reasons.append("counter_value not nonnegative integer")
            except(ValueError,TypeError):reasons.append("invalid counter_value");number=None
            unit=row.get("counter_unit","").strip()
            if unit not in ALLOWED_UNITS:reasons.append("unsupported unit")
            confidence=row.get("observation_confidence","").strip()
            if confidence not in ALLOWED_CONFIDENCE:reasons.append("unsupported confidence")
            method=row.get("collection_method","").strip()
            if method not in ALLOWED_METHOD:reasons.append("unapproved collection method")
            verified=row.get("rules_verified","").strip().lower()
            if verified not in {"yes","no"}:reasons.append("rules_verified must be yes/no")
            for field in ("venue_id","machine_model","model_revision","machine_number","counter_label","event_label"):
                val=str(row.get(field) or "")
                if len(val)>180 or DANGEROUS_FORMULA.search(val):reasons.append("unsafe "+field)
            label=str(row.get("event_label") or "").strip()
            normalized=LABELS.get(label.casefold(),"unknown")
            if normalized=="unknown":reasons.append("event mapping unverified")
            # An observed display like '単発' is still not evidence of actual ST or AT exit state.
            if normalized in {"claimed_run_through","claimed_single","claimed_reset"}:
                reasons.append("claimed state needs independent outcome verification")
            if verified!="yes":reasons.append("counter rules unverified")
            # Even verified row should not be used to infer hidden setting or zone probabilities.
            out={
                "line":i,"venue_id":str(row.get("venue_id") or "").strip()[:90],
                "machine_model":str(row.get("machine_model") or "").strip()[:120],
                "model_revision":str(row.get("model_revision") or "").strip()[:70],
                "data_date":str(row.get("data_date") or "").strip(),
                "machine_number":str(row.get("machine_number") or "").strip()[:35],
                "counter_label":str(row.get("counter_label") or "").strip()[:100],
                "counter_value":int(number) if number is not None else None,
                "counter_unit":unit,
                "event_label":label[:100],"event_type":normalized,
                "event_order":str(row.get("event_order") or "").strip()[:35],
                "source_url":str(row.get("source_url") or "").strip()[:360],
                "collection_method":method,
                "observation_confidence":confidence,
                "rules_verified":verified=="yes",
            }
            if not out["source_url"].startswith("https://"):reasons.append("missing https evidence URL")
            if reasons:held.append({"line":i,"reasons":sorted(set(reasons)),"record":out})
            else:accepted.append(out)
    return accepted,held


def run(path:Path, output:Path):
    ok,held=parse_csv(path)
    report={"schema":1,"pipeline":"counter-audit-only","notice":"This is not a performance estimate. Hall counter event names do not establish CZ/AT/ST boundaries without independent verification.","accepted_count":len(ok),"held_count":len(held),"accepted":ok,"hold_for_review":held}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("validated",len(ok),"rows; held",len(held),"for manual review")


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("input_csv",type=Path)
    p.add_argument("--output",type=Path,default=ROOT/"tmp"/"counter-audit.json")
    a=p.parse_args()
    run(a.input_csv,a.output)
