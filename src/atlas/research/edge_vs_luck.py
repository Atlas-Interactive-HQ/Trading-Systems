"""Placebo / block-bootstrap + stress matrix (phase1/103).

Registered for Mid #71 and Scalp S1 AFTER SHADOW exists. Not scored here.
S1 DEV Δ was tiny (~€1.46 on panel net vs #83; see phase1/87). Treat the
margin of safety as small until stress.
"""

from __future__ import annotations

from typing import Any, Sequence

EDGE_FRAMEWORK_ID = "edge_vs_luck_placebo_block_bootstrap_v1"
EDGE_CONFIRMED_PERCENTILE = 90
EDGE_STRONG_PERCENTILE = 95
# INCONCLUSIVE when observed expectancy is at or below the 90th placebo percentile.
FAMILIES_REGISTERED: tuple[str, ...] = ("mid_71", "scalp_s1")
S1_DEV_PANEL_NET_DELTA_EUR = 1.4637  # measured phase1/87; not a new score
S1_MARGIN_OF_SAFETY = "small_until_stress"

STRESS_MATRIX: tuple[str, ...] = (
    "costs_1_5x",
    "costs_2x",
    "next_open_plus_1_bar",
    "adverse_slip",
    "block_bootstrap",
    "placebo_timing",
    "chronological_shadow",
)


def classify_edge(
    observed_expectancy: float | None,
    placebo_expectancies: Sequence[float] | None,
    *,
    shadow_locked: bool,
) -> dict[str, Any]:
    """Classify only after SHADOW exists. Otherwise not_scored."""
    if not shadow_locked:
        return {
            "verdict": "not_scored",
            "reason": "SHADOW not locked — refuse to score edge-vs-luck",
            "framework": EDGE_FRAMEWORK_ID,
            "families": list(FAMILIES_REGISTERED),
            "not_a_forecast": True,
            "place_orders": False,
        }
    if observed_expectancy is None or not placebo_expectancies:
        return {
            "verdict": "insufficient_data",
            "reason": "need observed expectancy and placebo distribution",
            "fail_closed": True,
            "not_a_forecast": True,
        }
    xs = sorted(float(x) for x in placebo_expectancies)
    p90 = _percentile(xs, EDGE_CONFIRMED_PERCENTILE)
    p95 = _percentile(xs, EDGE_STRONG_PERCENTILE)
    obs = float(observed_expectancy)
    if obs > p95:
        verdict = "STRONG"
    elif obs > p90:
        verdict = "EDGE_CONFIRMED"
    else:
        verdict = "INCONCLUSIVE"
    return {
        "verdict": verdict,
        "observed_expectancy": obs,
        "placebo_p90": p90,
        "placebo_p95": p95,
        "n_placebo": len(xs),
        "rule": (
            "EDGE CONFIRMED if observed > 90th percentile placebo; "
            "STRONG if >95; INCONCLUSIVE if ≤90"
        ),
        "not_a_forecast": True,
        "place_orders": False,
        "soft_pass_neq_arm": True,
    }


def _percentile(sorted_xs: Sequence[float], p: float) -> float:
    if not sorted_xs:
        raise ValueError("empty placebo")
    if len(sorted_xs) == 1:
        return float(sorted_xs[0])
    idx = (p / 100.0) * (len(sorted_xs) - 1)
    lo = int(idx)
    hi = min(lo + 1, len(sorted_xs) - 1)
    frac = idx - lo
    return float(sorted_xs[lo]) * (1.0 - frac) + float(sorted_xs[hi]) * frac


def stress_plan() -> dict[str, Any]:
    return {
        "framework": EDGE_FRAMEWORK_ID,
        "families": list(FAMILIES_REGISTERED),
        "after": "contiguous_SHADOW_lock",
        "scored": False,
        "stress_is_not_a_new_strategy": True,
        "matrix": list(STRESS_MATRIX),
        "s1_dev_panel_net_delta_eur_cited": S1_DEV_PANEL_NET_DELTA_EUR,
        "s1_delta_source": "phase1/87",
        "s1_margin_of_safety": S1_MARGIN_OF_SAFETY,
        "no_hyperopt": True,
        "not_a_forecast": True,
        "place_orders": False,
        "soft_pass_neq_arm": True,
    }
