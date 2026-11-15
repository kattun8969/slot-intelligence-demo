"""Observed-only setting-stratified sensitivity analysis; never a strategy EV.

Setting labels are verified per episode and scenario weights are explicit inputs.
"""
from __future__ import annotations
from collections import defaultdict
from math import sqrt
from statistics import mean, stdev
from typing import Any
from scripts.ev_engine_core import InvalidEpisode
from scripts.ev_observed_episode_provenance import validate_observed_episode

class SensitivityError(ValueError):
    pass

def analyze_setting_sensitivity(rows: list[dict[str, Any]], scenarios: dict[str, dict[str, float]], *, min_per_setting: int = 10) -> dict[str, Any]:
    if isinstance(min_per_setting, bool) or not isinstance(min_per_setting, int) or min_per_setting < 2:
        raise SensitivityError("invalid_min_per_setting")
    if not isinstance(scenarios, dict) or not scenarios:
        raise SensitivityError("scenarios_required")
    observed: dict[str, list[float]] = defaultdict(list)
    identities = set()
    condition = None
    for row in rows:
        e = validate_observed_episode(row)
        setting = row.get("verified_setting")
        if isinstance(setting, bool) or not isinstance(setting, int) or not 1 <= setting <= 6:
            raise SensitivityError("verified_setting_1_to_6_required")
        if row.get("setting_evidence_status") != "verified":
            raise SensitivityError("setting_must_be_verified")
        key = (row["source_id"], e["venue_id"], e["date"], e["episode_id"])
        if key in identities:
            raise InvalidEpisode("duplicate episode")
        identities.add(key)
        current = (e["machine_id"],e["model_revision"],e["counter_type"],
                   row["counter_origin"],e["counter_value"],e["state"],
                   e["exchange_basis"],e["play_end_condition"])
        if condition is None:
            condition = current
        elif current != condition:
            raise SensitivityError("mixed_play_conditions")
        observed[str(setting)].append(e["net_yen"])
    stats = {}
    for setting, values in sorted(observed.items()):
        n=len(values)
        se=stdev(values)/sqrt(n) if n>1 else None
        stats[setting]={"sample_size":n,"mean_net_yen":round(mean(values),2),
                        "standard_error_yen":round(se,2) if se is not None else None,
                        "minimum_sample_met":n>=min_per_setting}
    scenario_results=[]
    for name, weights in sorted(scenarios.items()):
        if not isinstance(name,str) or not name.strip() or not isinstance(weights,dict) or not weights:
            raise SensitivityError("invalid_scenario")
        if any(str(k) not in {str(i) for i in range(1,7)} or isinstance(v,bool)
               or not isinstance(v,(int,float)) or not 0<=v<=1 for k,v in weights.items()):
            raise SensitivityError("invalid_setting_weight")
        if abs(sum(weights.values())-1.0)>1e-9:
            raise SensitivityError("scenario_weights_must_sum_to_one")
        missing=sorted(str(k) for k,v in weights.items() if v>0 and str(k) not in stats)
        insufficient=sorted(str(k) for k,v in weights.items() if v>0 and str(k) in stats
                            and not stats[str(k)]["minimum_sample_met"])
        eligible=not missing and not insufficient
        weighted=(sum(v*stats[str(k)]["mean_net_yen"] for k,v in weights.items())
                  if eligible else None)
        scenario_results.append({"name":name,"weights":{str(k):v for k,v in sorted(weights.items())},
                                 "missing_settings":missing,"insufficient_settings":insufficient,
                                 "weighted_observed_mean_yen":round(weighted,2) if weighted is not None else None,
                                 "scenario_calculable":eligible,
                                 "scenario_is_verified_real_world_distribution":False})
    return {"schema":1,"kind":"ev-setting-sensitivity","condition":condition,
            "per_setting":stats,"scenarios":scenario_results,
            "publication_status":"research_only","strategy_ev_verified":False,
            "notice":"Scenario weights are hypothetical, not actual hall setting allocations; observational means are not causal EV."}
