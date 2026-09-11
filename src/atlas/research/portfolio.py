"""Portfolio philosophy + CORE-MAJOR-v1 later hypothesis (phase1/105).

STRATEGY GREEN ≠ PORTFOLIO GREEN.
A sleeve without validated edge → allocation 0 / CASH (valid).
CORE-MAJOR is registered as later — not scored now; no R1–R7 coin-pick.
"""

from __future__ import annotations

from typing import Any

STRATEGY_GREEN_IS_NOT_PORTFOLIO_GREEN = True
UNVALIDATED_SLEEVE_ALLOCATION = 0.0
CASH_IS_VALID_ALLOCATION = True

CORE_MAJOR_V1: dict[str, Any] = {
    "id": "core_major_v1_btc_eth_identical_params_slow_trend_vol_targeted",
    "assets": ("BTC", "ETH"),
    "identical_params": True,
    "style": "slow_trend",
    "sizing": "vol_targeted",
    "status": "later_hypothesis_not_scored",
    "prereq": (
        "mid_71_contiguous_SHADOW",
        "scalp_s1_contiguous_SHADOW",
        "edge_vs_luck_and_stress",
    ),
    "r1_r7_coin_pick_forbidden": True,
    "scored": False,
}


def portfolio_card() -> dict[str, Any]:
    return {
        "strategy_green_is_not_portfolio_green": STRATEGY_GREEN_IS_NOT_PORTFOLIO_GREEN,
        "unvalidated_sleeve_allocation": UNVALIDATED_SLEEVE_ALLOCATION,
        "cash_is_valid_allocation": CASH_IS_VALID_ALLOCATION,
        "core_major_v1": {
            **CORE_MAJOR_V1,
            "assets": list(CORE_MAJOR_V1["assets"]),
            "prereq": list(CORE_MAJOR_V1["prereq"]),
        },
        "not_a_forecast": True,
        "place_orders": False,
        "soft_pass_neq_arm": True,
        "no_hyperopt": True,
    }


def sleeve_allocation(*, validated_edge: bool) -> dict[str, Any]:
    if validated_edge:
        return {
            "allocation": None,
            "reason": "size is a later portfolio decision; not scored here",
            "strategy_green_is_not_portfolio_green": True,
            "not_a_forecast": True,
        }
    return {
        "allocation": UNVALIDATED_SLEEVE_ALLOCATION,
        "cash": True,
        "reason": "sleeve without validated edge → 0 / CASH (valid)",
        "cash_is_valid_allocation": True,
        "not_a_forecast": True,
        "place_orders": False,
    }
