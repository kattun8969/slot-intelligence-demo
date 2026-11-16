"""Scenario ranges are sensitivity envelopes, never statistical confidence intervals."""
from scripts.ev_joint_outcomes import summarize_model

METRICS = ("expected_net_yen", "episode_win_probability", "at_mean_medals",
           "at_median_medals", "at_over_1000_probability")

def compare_scenarios(scenarios, *, scope):
    """scope fixes machine, setting, counter, start/end and exchange conditions.
    Alternative uncertain probability assumptions may vary; scope must not.
    """
    required = ("machine_id", "setting", "counter", "start_condition", "end_condition", "exchange")
    if not isinstance(scope, dict) or any(k not in scope or scope[k] in (None, "") for k in required):
        raise ValueError("complete scope required; use explicit unknown if setting unknown")
    if not scenarios:
        raise ValueError("scenarios required")
    results = []
    names = set()
    for scenario in scenarios:
        name = scenario["name"]
        if not isinstance(name, str) or not name.strip() or name in names:
            raise ValueError("unique scenario names required")
        names.add(name)
        result = summarize_model(scenario["outcomes"], revision=scenario["revision"],
                                 assumptions=scenario["assumptions"], sources=scenario["sources"])
        results.append(dict(name=name, **result))
    return {"scope": dict(scope), "scenarios": results,
            "range_kind": "assumption_sensitivity_not_confidence_interval",
            "ranges": {key: {"low": min(r[key] for r in results),
                             "high": max(r[key] for r in results)} for key in METRICS}}
