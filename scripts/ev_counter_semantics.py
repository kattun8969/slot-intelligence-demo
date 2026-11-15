"""Explicit signed-difference vs nonnegative game counter semantics.

This standalone module validates *observed display values*, not inferred EV.
Do not infer reset events from a decrease in daily/section difference medals.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

NONNEGATIVE_COUNTERS = frozenset({
    "at_games", "cz_games", "bonus_games", "cycle_number",
    "cycle_games", "screen_points",
})
SIGNED_COUNTERS = frozenset({"daily_difference_medals", "section_difference_medals"})
ALL_COUNTERS = NONNEGATIVE_COUNTERS | SIGNED_COUNTERS

class CounterSemanticsError(ValueError):
    pass

def validate_counter_value(counter_type: str, value: Any) -> int:
    if counter_type not in ALL_COUNTERS:
        raise CounterSemanticsError("unknown_counter_type")
    if isinstance(value, bool) or not isinstance(value, int):
        raise CounterSemanticsError("counter_value_must_be_integer")
    if counter_type in NONNEGATIVE_COUNTERS and value < 0:
        raise CounterSemanticsError("negative_game_or_point_counter")
    return value

def parse_counter_value(counter_type: str, raw: str) -> int:
    if not isinstance(raw, str) or not raw:
        raise CounterSemanticsError("missing_counter_value")
    # Preserve strict ASCII digits; reject comma separators, decimals,
    # Unicode lookalikes, surrounding whitespace and explicit plus signs.
    negative = raw.startswith("-")
    digits = raw[1:] if negative else raw
    if not digits or not all("0" <= c <= "9" for c in digits):
        raise CounterSemanticsError("invalid_counter_integer")
    if len(digits) > 1 and digits[0] == "0":
        raise CounterSemanticsError("noncanonical_counter_integer")
    if negative and digits == "0":
        raise CounterSemanticsError("negative_zero")
    return validate_counter_value(counter_type, int(raw))

@dataclass(frozen=True)
class CounterTransition:
    counter_type: str
    previous: int
    current: int
    same_origin: bool
    classification: str
    needs_review: bool
    reason: str

def inspect_transition(
    counter_type: str, previous: int, current: int, *,
    previous_origin: str, current_origin: str,
    boundary_evidence: str = "none",
) -> CounterTransition:
    """Do not call a decrease a reset without verified boundary evidence."""
    validate_counter_value(counter_type, previous)
    validate_counter_value(counter_type, current)
    if not previous_origin or not current_origin:
        raise CounterSemanticsError("counter_origin_required")
    if boundary_evidence not in {"none", "verified_reset", "verified_cycle_boundary", "verified_at_end", "verified_cz_end"}:
        raise CounterSemanticsError("unknown_boundary_evidence")
    same = previous_origin == current_origin
    if counter_type in SIGNED_COUNTERS:
        return CounterTransition(
            counter_type, previous, current, same,
            "signed_difference_changed" if previous != current else "unchanged",
            not same,
            "signed difference movement alone is not a reset signal; origin changes require review" if not same
            else "signed difference can increase or decrease without a counter reset",
        )
    if not same:
        return CounterTransition(counter_type, previous, current, False,
                                 "origin_changed", True,
                                 "different counter origins cannot be compared as one sequence")
    if current < previous:
        if boundary_evidence != "none":
            return CounterTransition(counter_type, previous, current, True,
                                     "decrease_with_boundary_evidence", True,
                                     "boundary evidence supplied; verify source and counter semantics")
        return CounterTransition(counter_type, previous, current, True,
                                 "unexplained_counter_decrease", True,
                                 "decrease without verified boundary evidence")
    return CounterTransition(counter_type, previous, current, True,
                             "nondecreasing", False,
                             "no decrease observed; continuity not proven")
