"""Exact joint-outcome model; probabilities are editorial assumptions, not observations."""
from math import isfinite
from statistics import fmean

def summarize_model(outcomes, *, revision, assumptions, sources):
    """Each outcome: probability, investment_yen, return_yen, at_medals.
    One complete strategy episode per outcome. AT medals must be scoped consistently.
    """
    if not revision or not assumptions or not sources or not outcomes:
        raise ValueError("revision, assumptions, sources and outcomes required")
    for row in outcomes:
        for key in ("probability", "investment_yen", "return_yen", "at_medals"):
            value = row[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value < 0:
                raise ValueError("invalid " + key)
    if abs(sum(r["probability"] for r in outcomes) - 1) > 1e-9:
        raise ValueError("probabilities must sum to one")
    ordered = sorted(outcomes, key=lambda r: r["at_medals"])
    cumulative = 0
    median = None
    for row in ordered:
        cumulative += row["probability"]
        if cumulative >= .5:
            median = row["at_medals"]
            break
    return {
        "model_revision": revision, "evidence_kind": "editorial_prediction",
        "assumptions": assumptions, "sources": sources,
        "expected_net_yen": sum(r["probability"] * (r["return_yen"] - r["investment_yen"]) for r in outcomes),
        "episode_win_probability": sum(r["probability"] for r in outcomes if r["return_yen"] > r["investment_yen"]),
        "at_mean_medals": sum(r["probability"] * r["at_medals"] for r in outcomes),
        "at_median_medals": median,
        "at_over_1000_probability": sum(r["probability"] for r in outcomes if r["at_medals"] >= 1000),
        "note": "Model conditional on supplied assumptions; not setting-specific unless inputs are. Zero payout is not automatically runthrough.",
    }
