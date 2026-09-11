"""SCALP-R2 first-score harness: walker gate, ids, no promote flags."""

from __future__ import annotations

from atlas.paper.rise_panel import SCALP_R2_HYPOTHESIS_ID
from atlas.paper.rise_panel_scalp_r2_4h_regime_1h_eval import (
    SCALP_R2_ID,
    SCALP_S1_ID,
    deltas_vs_scalp_s1,
    render_results_markdown,
)
from atlas.strategy.scalp_doge_dual_thrust_rvol_4h_regime_1h import (
    FAMILY,
    LADDER_ID,
    ScalpDogeDualThrustRvol4hRegime1hV1,
)


def test_ids_locked():
    assert SCALP_R2_ID == SCALP_R2_HYPOTHESIS_ID
    assert SCALP_R2_ID == "rise_panel_v1_scalp_r2_dual_thrust_4h_ema1221_regime"
    assert LADDER_ID == "SCALP-R2"
    assert "4h_ema1221_regime" in FAMILY


def test_strategy_refuses_long_flat_api():
    s = ScalpDogeDualThrustRvol4hRegime1hV1()
    try:
        s.desired_state([])
        raise AssertionError("desired_state must raise")
    except RuntimeError as exc:
        assert "walk_long_flat" in str(exc)


def test_deltas_never_promote():
    empty = {
        "old_summary": {"panel_net_eur": 1.0, "median_expectancy_eur": 0.1},
        "v2_summary": {
            "panel_terminal_liquidation_net_eur": 1.0,
            "n_exp_terminal_adj_gt_0": 6,
            "n_forced_window_close": 0,
        },
        "completed_summary": {
            "median_expectancy_completed_eur": 0.1,
            "n_expectancy_completed_gt_0": 6,
            "median_completed_round_trips": 5,
            "worst_dd_eur": 1.0,
            "median_time_in_market": 0.2,
            "sum_n_entries": 10,
            "sum_n_long_entries": 6,
            "sum_n_short_entries": 4,
        },
        "accounting_v2": {"verdict": "PASS"},
        "soft_promote_v1_unchanged": {"verdict": "PASS"},
        "rows": [],
    }
    d = deltas_vs_scalp_s1(empty, empty)
    assert d["promote"] is False
    assert d["promote_as_better"] is False
    assert d["soft_pass_ne_scalp_arm"] is True
    assert d["no_rvol_grind"] is True
    assert d["walker"] == "walk_long_short"
    assert SCALP_S1_ID in d["compare_to"]


def test_markdown_mentions_hard_rules():
    empty = {
        "old_summary": {},
        "v2_summary": {},
        "completed_summary": {},
        "accounting_v2": {"verdict": "FAIL"},
        "soft_promote_v1_unchanged": {"verdict": "FAIL"},
        "rows": [],
        "deltas": [],
    }
    md = render_results_markdown(empty, empty)
    assert "walk_long_flat" in md
    assert "Soft PASS ≠ Scalp-arm" in md
    assert "does not promote" in md.lower() or "no promote" in md.lower()
    assert "99" in md
    assert "HALTED" in md
    assert "not_a_forecast" in md
