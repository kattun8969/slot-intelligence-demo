"""Audit discovered new machines against cited EV reference rows.

Read-only. A reference row is NOT proof of a live, machine-specific EV table.
"""
from __future__ import annotations
import argparse
import json
from datetime import date, datetime, time
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DISCOVERY = ROOT / "docs" / "auto-machine-discovery.json"
REFERENCE = ROOT / "docs" / "public-ev-reference.json"

# Exact catalog IDs only: never match by a substring of a machine name.
CATALOG_TO_REFERENCE = {
    "7489": "vivy",
    "7455": "ragnador",
    "7450": "seiya",
    "7446": "ggo",
}

def valid_scenario(s):
    if not isinstance(s, dict) or not all(isinstance(s.get(k),str) and s[k].strip()
        for k in ("id","machine","label","counter","state","exit","price","source_name","url","checked_at")):
        return False
    u=urlparse(s["url"])
    if u.scheme != "https" or not u.hostname or u.username or u.password:
        return False
    try:
        if date.fromisoformat(s["checked_at"]).isoformat()!=s["checked_at"]:
            return False
    except ValueError:
        return False
    p=s.get("points")
    if not isinstance(p,list) or len(p)<2 or not isinstance(s.get("preconditions"),list) or not s["preconditions"]:
        return False
    previous=-1
    for point in p:
        if not isinstance(point,list) or len(point)!=2:
            return False
        x,y=point
        if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not float("-inf")<v<float("inf") for v in (x,y)):
            return False
        if x<0 or x<=previous:
            return False
        previous=x
    return True

def coverage(discovery, reference, *, as_of):
    if not isinstance(discovery.get("machines"),list) or not isinstance(reference.get("scenarios"),list):
        raise ValueError("invalid inputs")
    ids=set()
    scenarios={}
    for row in reference["scenarios"]:
        if valid_scenario(row):
            scenarios.setdefault(row["machine"],[]).append(row["id"])
    output=[]
    for machine in discovery["machines"]:
        catalog_id=str(machine["id"])
        if catalog_id in ids:
            raise ValueError("duplicate catalog id")
        ids.add(catalog_id)
        first=date.fromisoformat(machine["first_seen"])
        # Date-only discovery has no known clock time. Warn only if breach is certain.
        latest=datetime.combine(first,time.max)
        now=datetime.combine(as_of,time.min)
        certain_age=(now-latest).total_seconds()/3600
        reference_id=CATALOG_TO_REFERENCE.get(catalog_id)
        matches=sorted(scenarios.get(reference_id,[])) if reference_id else []
        output.append({
            "catalog_id":catalog_id,"machine_name":machine["name"],
            "catalog_url":machine["url"],"first_seen":machine["first_seen"],
            "elapsed_hours":None,"age_precision":"date_only",
            "reference_machine_id":reference_id,
            "valid_reference_scenario_ids":matches,
            "reference_rows_available":bool(matches),
            "machine_page_table_verified":False,
            "live_pages_verified":False,
            "publication_status":"unverified",
            "needs_source_research":not bool(matches),
            "target_18h_warning":certain_age>=18,
            "target_24h_exceeded":certain_age>=24,
        })
    return {"schema":1,"as_of":as_of.isoformat(),"machine_count":len(output),
            "reference_rows_available_count":sum(x["reference_rows_available"] for x in output),
            "live_machine_tables_verified_count":0,
            "machines":output,
            "notice":"Reference rows are not evidence of live machine-page tables; verify deployed HTML separately."}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--as-of",default=date.today().isoformat())
    args=parser.parse_args()
    with DISCOVERY.open(encoding="utf-8") as f:
        discovery=json.load(f)
    with REFERENCE.open(encoding="utf-8") as f:
        reference=json.load(f)
    print(json.dumps(coverage(discovery,reference,as_of=date.fromisoformat(args.as_of)),
                     ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
