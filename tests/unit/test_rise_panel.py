"""Unit tests: rise_panel_v1 locked windows + soft-promote scoring helpers."""

from __future__ import annotations

from atlas.paper.cascade import CORE_START_EUR, MID_START_EUR
from atlas.paper.rise_panel import (
    ASSET,
    BASELINE_ID,
    CORE_BAR,
    CORE_DONCHIAN_FAMILY_STOPPED,
    CORE_R1_ID,
    MID_BAR_CANDIDATE,
    MID_BASELINE_ID,
    MID_BREAKOUT_ARCHIVE_ID,
    MID_CANDIDATE_ID,
    MID_EMA_ARCHIVE_ID,
    MID_M1_COMPARATOR_ID,
    MID_M1_ROLE,
    MID_NEXT_SCORE,
    MID_PRIMARY_CANDIDATE_ID,
    PANEL_LABEL,
    RISE_PANEL_V1,
    SCALP_PROVISIONAL_DEV_ID,
    SCALP_R2_HYPOTHESIS_ID,
    SCALP_S0_ID,
    SOFT_PROMOTE_GATE,
    SOFT_PROMOTE_MEDIAN_TRADES_MIN,
    SOFT_PROMOTE_MIN_EXP_POS,
    justification_rows,
    panel_summary_table,
    panel_windows,
    soft_promote_score,
    window_by_id,
)


def test_panel_locked_seven_windows():
    wins = panel_windows()
    assert len(wins) == 7
    assert len(RISE_PANEL_V1) == 7
    assert PANEL_LABEL == "rise_panel_v1"
    assert ASSET == "DOGE-USDT"
    assert CORE_BAR == "1D"
    assert MID_BAR_CANDIDATE == "4H"
    ids = [w.id for w in wins]
    assert ids == ["R1", "R2", "R3", "R4", "R5", "R6", "R7"]


def test_window_dates_and_justification_non_invented():
    """Dates locked; approx % are documented floats from MD (not None / not 0 placeholders)."""
    rows = justification_rows()
    assert len(rows) == 7
    r1 = window_by_id("R1")
    assert r1.start == "2020-10-01" and r1.end == "2020-12-31"
    assert r1.approx_move_pct == 87.1
    r7 = window_by_id("R7")
    assert r7.start == "2024-08-07" and r7.end == "2024-11-04"
    assert r7.approx_move_pct == 78.0
    # Non-overlapping chronological order
    starts = [w.start for w in RISE_PANEL_V1]
    assert starts == sorted(starts)
    for w in RISE_PANEL_V1:
        assert w.approx_move_pct > 0
        assert w.start < w.end
        assert "→" in w.label or w.start in w.label


def test_window_ms_exclusive_end():
    w = window_by_id("R4")
    # inclusive end 2023-11-30 → exclusive = 2023-12-01 00:00 UTC
    assert w.end_ms_exclusive > w.start_ms
    day_ms = 24 * 60 * 60 * 1000
    # ~91 days inclusive
    span_days = (w.end_ms_exclusive - w.start_ms) / day_ms
    assert 90 <= span_days <= 93


def test_ids_and_sleeves():
    assert BASELINE_ID == "rise_panel_v1_core_doge_ema12_30_1d_eur140"
    assert MID_CANDIDATE_ID == "rise_panel_v1_mid_doge_ema12_30_4h_eur40"
    assert MID_EMA_ARCHIVE_ID == MID_CANDIDATE_ID
    assert MID_BASELINE_ID == "rise_panel_v1_mid_doge_breakoutv1_ema1221_long_4h_eur40"
    assert MID_BREAKOUT_ARCHIVE_ID == "rise_panel_v1_mid_doge_breakoutv1_4h_eur40"
    assert CORE_START_EUR == 140.0
    assert MID_START_EUR == 40.0


def test_p2_p3_freeze_constants():
    assert MID_PRIMARY_CANDIDATE_ID == MID_BASELINE_ID
    assert MID_M1_COMPARATOR_ID.endswith("adx14_gt20_4h_eur40")
    assert MID_M1_ROLE == "robustness_comparator_only"
    assert MID_NEXT_SCORE == "unseen_SHADOW_only"
    assert SCALP_PROVISIONAL_DEV_ID.endswith("rvol_gt1_1h_eur20")
    assert SCALP_S0_ID.endswith("k0505_1h_eur20")
    assert SCALP_R2_HYPOTHESIS_ID == "rise_panel_v1_scalp_r2_dual_thrust_4h_ema1221_regime"
    assert CORE_DONCHIAN_FAMILY_STOPPED is True
    assert CORE_R1_ID == "rise_panel_v1_core_r1_doge_ema12_30_atr14_trail3_1d_eur140"


def test_soft_promote_pass():
    rows = [
        {"n_trades": 4, "expectancy_after_costs_eur": 0.5, "net_return_eur": 2.0, "max_dd_eur": 1.0},
        {"n_trades": 3, "expectancy_after_costs_eur": 0.2, "net_return_eur": 0.6, "max_dd_eur": 2.0},
        {"n_trades": 5, "expectancy_after_costs_eur": 0.1, "net_return_eur": 0.5, "max_dd_eur": 1.5},
        {"n_trades": 2, "expectancy_after_costs_eur": 0.3, "net_return_eur": 0.6, "max_dd_eur": 3.0},
        {"n_trades": 6, "expectancy_after_costs_eur": 0.4, "net_return_eur": 2.4, "max_dd_eur": 2.2},
        {"n_trades": 1, "expectancy_after_costs_eur": -0.1, "net_return_eur": -0.1, "max_dd_eur": 4.0},
        {"n_trades": 3, "expectancy_after_costs_eur": 0.15, "net_return_eur": 0.45, "max_dd_eur": 1.1},
    ]
    sc = soft_promote_score(rows)
    assert sc["gate"] == SOFT_PROMOTE_GATE
    assert sc["differs_from_core_style_ab"] is True
    assert sc["median_trades"] == 3
    assert sc["median_trades_ok"] is True
    assert sc["n_expectancy_gt_0"] == 6
    assert sc["expectancy_gt_0_ok"] is True
    assert sc["panel_net_ok"] is True
    assert sc["pass"] is True
    assert sc["verdict"] == "PASS"
    assert sc["worst_dd_eur"] == 4.0


def test_soft_promote_fail_low_median_trades():
    """n≈0 BH-twin style — median_trades not ≫ 0."""
    rows = [
        {"n_trades": 0, "expectancy_after_costs_eur": None, "net_return_eur": 5.0, "max_dd_eur": 1.0},
        {"n_trades": 0, "expectancy_after_costs_eur": None, "net_return_eur": 4.0, "max_dd_eur": 1.0},
        {"n_trades": 0, "expectancy_after_costs_eur": None, "net_return_eur": 3.0, "max_dd_eur": 1.0},
        {"n_trades": 0, "expectancy_after_costs_eur": None, "net_return_eur": 2.0, "max_dd_eur": 1.0},
        {"n_trades": 0, "expectancy_after_costs_eur": None, "net_return_eur": 1.0, "max_dd_eur": 1.0},
        {"n_trades": 0, "expectancy_after_costs_eur": None, "net_return_eur": 1.0, "max_dd_eur": 1.0},
        {"n_trades": 1, "expectancy_after_costs_eur": 0.5, "net_return_eur": 0.5, "max_dd_eur": 1.0},
    ]
    sc = soft_promote_score(rows)
    assert sc["median_trades"] == 0
    assert sc["median_trades_ok"] is False
    assert sc["n_expectancy_gt_0"] == 1
    assert sc["expectancy_gt_0_ok"] is False
    assert sc["pass"] is False
    assert sc["verdict"] == "FAIL"


def test_soft_promote_fail_panel_net():
    rows = [
        {"n_trades": 3, "expectancy_after_costs_eur": 0.1, "net_return_eur": 0.3, "max_dd_eur": 1.0},
        {"n_trades": 3, "expectancy_after_costs_eur": 0.1, "net_return_eur": 0.3, "max_dd_eur": 1.0},
        {"n_trades": 3, "expectancy_after_costs_eur": 0.1, "net_return_eur": 0.3, "max_dd_eur": 1.0},
        {"n_trades": 3, "expectancy_after_costs_eur": 0.1, "net_return_eur": 0.3, "max_dd_eur": 1.0},
        {"n_trades": 3, "expectancy_after_costs_eur": 0.1, "net_return_eur": 0.3, "max_dd_eur": 1.0},
        {"n_trades": 3, "expectancy_after_costs_eur": -2.0, "net_return_eur": -6.0, "max_dd_eur": 5.0},
        {"n_trades": 3, "expectancy_after_costs_eur": -2.0, "net_return_eur": -6.0, "max_dd_eur": 5.0},
    ]
    sc = soft_promote_score(rows)
    assert sc["n_expectancy_gt_0"] == 5
    assert sc["expectancy_gt_0_ok"] is True
    assert sc["median_trades_ok"] is True
    assert sc["panel_net_ok"] is False
    assert sc["pass"] is False


def test_soft_promote_thresholds_locked():
    assert SOFT_PROMOTE_MIN_EXP_POS == 5
    assert SOFT_PROMOTE_MEDIAN_TRADES_MIN == 1
    assert SOFT_PROMOTE_GATE == "soft_promote_v1"


def test_panel_summary_wraps_soft():
    rows = [
        {"n_trades": 2, "expectancy_after_costs_eur": 1.0, "net_return_eur": 2.0, "max_dd_eur": 0.5}
    ] * 7
    summary = panel_summary_table(rows)
    assert summary["panel"] == PANEL_LABEL
    assert summary["n_exp_gt_0"] == 7
    assert summary["soft_promote"]["pass"] is True
    assert summary["place_orders"] is False
    assert summary["not_a_forecast"] is True
