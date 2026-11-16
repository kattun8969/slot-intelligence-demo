"""Explicit conditional hazards; no machine hazard is inferred from mean hit rate."""
from math import isfinite

def build_episodes(hazards, payout_support, *, yen_per_game, yen_per_medal):
    """hazards[i] is hit probability on future game i+1 given survival.
    Final hazard must be one (explicit modeled ceiling); payouts are assumed
    independent of time to hit. Costs are net expected costs, not cash outlay.
    """
    def valid(x):
        return not isinstance(x,bool) and isinstance(x,(int,float)) and isfinite(x) and x>=0
    if not hazards or any(not valid(h) or h>1 for h in hazards) or hazards[-1]!=1:
        raise ValueError("bounded hazards with explicit final ceiling required")
    if not valid(yen_per_game) or not valid(yen_per_medal) or yen_per_medal==0:
        raise ValueError("invalid cost/exchange")
    if not payout_support or any(not valid(r["probability"]) or not valid(r["at_medals"]) for r in payout_support):
        raise ValueError("invalid payout support")
    if abs(sum(r["probability"] for r in payout_support)-1)>1e-9:
        raise ValueError("payout probability sum")
    survival=1.
    outcomes=[]
    for games,h in enumerate(hazards,1):
        hit=survival*h
        if hit:
            for r in payout_support:
                if r["probability"]:
                    outcomes.append(dict(probability=hit*r["probability"],
                        investment_yen=games*yen_per_game,
                        return_yen=r["at_medals"]*yen_per_medal,
                        at_medals=r["at_medals"]))
        survival*=1-h
    return outcomes
