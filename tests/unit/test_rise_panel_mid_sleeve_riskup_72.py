"""Unit tests: rise_panel Mid #72 sleeve RISK-UP €60 lock + linearity deltas."""

from __future__ import annotations

import pytest

from atlas.paper.cascade import CORE_START_EUR, MID_START_EUR
from atlas.paper.rise_panel import (
    MID_BASELINE_ID,
    MID_BREAKOUT_ARCHIVE_ID,
    MID_EMA_ARCHIVE_ID,
    PANEL_LABEL,
    RISE_PANEL_V1,
    soft_promote_score,
)
from atlas.paper.rise_panel_mid_sleeve_riskup_72_eval import (
    CORE_MID_BOOK_EUR,
    CORE_MID_BOOK_ID,
    MID_71_BASELINE_ID,
    MID_RISKUP_ID,
    MID_SLEEVE_EUR40,
    MID_SLEEVE_EUR60,
    SIZE_MULT,
    deltas_vs_mid_71,
)
from atlas.strategy.mid_doge_breakout_ema1221_4h import (
    ATR_PERIOD,
    BAR,
    EMA_FAST,
    EMA_SLOW,
    FAMILY,
    LOOKBACK,
    MIN_ATR_FRAC,
    SLEEVE,
    MidDogeBreakoutEma1221V1,
)


def test_ids_and_sleeve_locked():
    assert MID_71_BASELINE_ID == MID_BASELINE_ID
    assert MID_BASELINE_ID == "rise_panel_v1_mid_doge_breakoutv1_ema1221_long_4h_eur40"
    assert MID_BREAKOUT_ARCHIVE_ID == "rise_panel_v1_mid_doge_breakoutv1_4h_eur40"
    assert MID_RISKUP_ID == "rise_panel_v1_mid_doge_breakoutv1_ema1221_long_4h_eur60"
    assert MID_START_EUR == 40.0
    assert MID_SLEEVE_EUR40 == 40.0
    assert MID_SLEEVE_EUR60 == 60.0
    assert SIZE_MULT == 1.5
    assert CORE_START_EUR == 140.0
    assert CORE_MID_BOOK_EUR == 200.0
    assert CORE_MID_BOOK_ID == "rise_panel_v1_core_mid_book_200_mid_breakout_ema1221_eur60"
    assert PANEL_LABEL == "rise_panel_v1"
    assert len(RISE_PANEL_V1) == 7
    assert MID_EMA_ARCHIVE_ID == "rise_panel_v1_mid_doge_ema12_30_4h_eur40"


def test_family_same_as_71():
    assert FAMILY == "breakout_v1_ema1221_long_regime_4h"
    assert BAR == "4H"
    assert LOOKBACK == 16
    assert ATR_PERIOD == 14
    assert MIN_ATR_FRAC == 0.001
    assert EMA_FAST == 12
    assert EMA_SLOW == 21
    assert SLEEVE == "mid"
    s = MidDogeBreakoutEma1221V1()
    assert "mid_doge_breakout_ema1221_4h" in s.label


def test_deltas_linearity_shape():
    baseline = {
        "summary": {
            "median_expectancy_eur": 2.0,
            "panel_net_eur": 100.0,
            "median_trades": 7.0,
            "n_exp_gt_0": 5,
            "worst_dd_eur": 20.0,
        }
    }
    # exact linear 1.5x
    linear = {
        "summary": {
            "median_expectancy_eur": 3.0,
            "panel_net_eur": 150.0,
            "median_trades": 7.0,
            "n_exp_gt_0": 5,
            "worst_dd_eur": 30.0,
        }
    }
    d = deltas_vs_mid_71(baseline, linear)
    assert d["compare_to"] == MID_71_BASELINE_ID
    assert d["riskup_id"] == MID_RISKUP_ID
    assert abs(d["panel_net_eur"]["delta"] - 50.0) < 1e-6
    assert abs(d["panel_net_eur"]["linear_1_5x"] - 150.0) < 1e-6
    assert abs(d["panel_net_eur"]["ratio_vs_linear"] - 1.0) < 1e-6
    assert d["promote_as_better"] is True

    # bigger € but sublinear (ratio < 0.95)
    sub = {
        "summary": {
            "median_expectancy_eur": 2.2,
            "panel_net_eur": 110.0,
            "median_trades": 7.0,
            "n_exp_gt_0": 5,
            "worst_dd_eur": 22.0,
        }
    }
    d2 = deltas_vs_mid_71(baseline, sub)
    assert d2["promote_as_better"] is False
    assert d2["panel_net_eur"]["delta"] > 0


def test_soft_promote_helper_still_works():
    rows = [
        {"ok": True, "n_trades": 5, "expectancy_after_costs_eur": 1.0, "net_return_eur": 5.0},
        {"ok": True, "n_trades": 4, "expectancy_after_costs_eur": 0.5, "net_return_eur": 2.0},
        {"ok": True, "n_trades": 6, "expectancy_after_costs_eur": 0.2, "net_return_eur": 1.0},
        {"ok": True, "n_trades": 3, "expectancy_after_costs_eur": 0.1, "net_return_eur": 0.5},
        {"ok": True, "n_trades": 7, "expectancy_after_costs_eur": 0.3, "net_return_eur": 2.0},
        {"ok": True, "n_trades": 2, "expectancy_after_costs_eur": -0.1, "net_return_eur": -0.2},
        {"ok": True, "n_trades": 8, "expectancy_after_costs_eur": 0.4, "net_return_eur": 3.0},
    ]
    soft = soft_promote_score(rows)
    assert soft["verdict"] == "PASS"
