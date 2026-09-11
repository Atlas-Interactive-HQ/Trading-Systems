"""Board execution-order lock (phase1/106). Register only — do not score."""

from __future__ import annotations

from typing import Any

HARD_INVARIANTS: tuple[str, ...] = (
    "not_a_forecast",
    "soft_pass_neq_arm",
    "live_le_eur20_halted",
    "r1_r7_dev_eliminate_only_paused",
    "no_post_hoc_winners",
    "no_hyperopt",
    "default_yaml_untouched",
    "do_not_invent_capture_numbers",
    "do_not_select_hft_instrument_in_this_pr",
    "do_not_score_strategies_in_this_pr",
)

# A → F as locked by the board before P4a metrics are used for selection.
BOARD_ORDER: tuple[tuple[str, str], ...] = (
    ("A", "governance_doctrine_lock"),
    ("B", "p4a_screening_then_p4b_7d_instrument_lock"),
    ("C", "shadow_contiguous_after_contamination_audit"),
    ("D", "robustness_mid71_and_s1_edge_vs_luck"),
    ("E", "hft_liquidity_signal_markout_then_pnl"),
    ("F", "core_major_only_afterwards"),
)

CURRENT_BOARD_STEP = "A"


def board_card() -> dict[str, Any]:
    return {
        "current_step": CURRENT_BOARD_STEP,
        "order": [{"step": s, "id": i} for s, i in BOARD_ORDER],
        "hard_invariants": list(HARD_INVARIANTS),
        "p4a_may_lock_instrument": False,
        "r1_r7_dev_eliminate_only_paused": True,
        "soft_pass_neq_arm": True,
        "live_le_eur20_halted": True,
        "no_hyperopt": True,
        "no_post_hoc_winners": True,
        "not_a_forecast": True,
        "place_orders": False,
        "default_yaml_untouched": True,
        "this_pr_scores_strategies": False,
        "this_pr_selects_hft_instrument": False,
    }
