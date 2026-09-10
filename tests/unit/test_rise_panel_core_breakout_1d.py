"""Unit tests: rise_panel Core #69 BreakoutV1 1D lock + soft-promote deltas."""

from __future__ import annotations

import pytest

from atlas.paper.cascade import CORE_START_EUR, MID_START_EUR
from atlas.paper.rise_panel import (
    BASELINE_ID,
    PANEL_LABEL,
    RISE_PANEL_V1,
    soft_promote_score,
)
from atlas.paper.rise_panel_core_breakout_1d_eval import (
    CORE_BASELINE_ID,
    CORE_EMA_SNAPSHOT_54,
    CORE_IMPROVE_ID,
    CORE_MID_BOOK_EUR,
    CORE_MID_BOOK_ID,
    MID_BREAKOUT_SNAPSHOT_65,
    deltas_vs_core_baseline,
)
from atlas.strategy.core_doge_breakout_1d import (
    ATR_PERIOD,
    BAR,
    FAMILY,
    FLAT,
    LONG,
    LOOKBACK,
    MIN_ATR_FRAC,
    SLEEVE,
    CoreDogeBreakout1dParams,
    CoreDogeBreakout1dV1,
)
from atlas.paper.types import Bar

BAR_MS = 24 * 60 * 60 * 1000
START = 1_600_000_000_000
SYM = "DOGE-USDT"


def _bar(i: int, c: float, h: float | None = None, lo: float | None = None) -> Bar:
    ts = START + i * BAR_MS
    hi = h if h is not None else c + 0.01
    low = lo if lo is not None else c - 0.01
    return Bar(SYM, ts, ts + BAR_MS, c, hi, low, c, 1.0, True, "test")


def test_ids_and_sleeve_locked():
    assert CORE_BASELINE_ID == BASELINE_ID
    assert CORE_BASELINE_ID == "rise_panel_v1_core_doge_ema12_30_1d_eur140"
    assert CORE_IMPROVE_ID == "rise_panel_v1_core_doge_breakoutv1_1d_eur140"
    assert CORE_START_EUR == 140.0
    assert MID_START_EUR == 40.0
    assert CORE_MID_BOOK_EUR == 180.0
    assert CORE_MID_BOOK_ID == "rise_panel_v1_core_mid_book_180_core_breakoutv1_1d"
    assert PANEL_LABEL == "rise_panel_v1"
    assert len(RISE_PANEL_V1) == 7
    # measured Core EMA snapshot — do not invent
    assert abs(CORE_EMA_SNAPSHOT_54["panel_net_eur"] - 363.9983) < 1e-4
    assert abs(MID_BREAKOUT_SNAPSHOT_65["panel_net_eur"] - 95.4483) < 1e-4


def test_family_breakout_locked():
    assert FAMILY == "breakout_v1_long_flat_1d"
    assert BAR == "1D"
    assert LOOKBACK == 16
    assert ATR_PERIOD == 14
    assert MIN_ATR_FRAC == 0.001
    assert SLEEVE == "core"
    s = CoreDogeBreakout1dV1()
    assert "core_doge_breakout_1d" in s.label
    assert s.warmup_bars() == max(LOOKBACK, ATR_PERIOD) + 1
    assert s.params.oneh_filter == "off"


def test_rejects_lookback_tf_sleeve_sweeps():
    with pytest.raises(ValueError, match="lookback"):
        CoreDogeBreakout1dV1(CoreDogeBreakout1dParams(lookback=20))
    with pytest.raises(ValueError, match="atr_period"):
        CoreDogeBreakout1dV1(CoreDogeBreakout1dParams(atr_period=10))
    with pytest.raises(ValueError, match="bar"):
        CoreDogeBreakout1dV1(CoreDogeBreakout1dParams(bar="4H"))
    with pytest.raises(ValueError, match="sleeve"):
        CoreDogeBreakout1dV1(CoreDogeBreakout1dParams(sleeve="mid"))
    with pytest.raises(ValueError, match="oneh_filter"):
        CoreDogeBreakout1dV1(CoreDogeBreakout1dParams(oneh_filter="stub"))


def test_entry_break_above_16_exit_below_16():
    """BreakoutV1 channel: break prior 16-high → long; break prior 16-low → flat."""
    bars = [_bar(i, 100.0 + 0.01 * (i % 3), h=101.0, lo=99.0) for i in range(20)]
    bars.append(_bar(20, 102.0, h=102.5, lo=100.0))  # close > prior highs
    strat = CoreDogeBreakout1dV1()
    assert strat.desired_state(bars) == LONG
    bars.append(_bar(21, 50.0, h=102.0, lo=49.0))
    assert strat.desired_state(bars) == FLAT


def test_never_short_and_no_ema_filter_attr():
    closes = [1.0 + 0.01 * i for i in range(80)]
    bars = [_bar(i, c, h=c + 0.05, lo=c - 0.05) for i, c in enumerate(closes)]
    strat = CoreDogeBreakout1dV1()
    for i in range(len(bars)):
        assert strat.desired_state(bars[: i + 1]) in (LONG, FLAT)
    assert not hasattr(strat, "set_daily_bars")
    assert not hasattr(strat, "ema_filter")


def test_deltas_vs_core_baseline_shape():
    baseline = {
        "summary": {
            "median_expectancy_eur": -2.9545,
            "panel_net_eur": 363.9983,
            "median_trades": 1.0,
            "n_exp_gt_0": 2,
        }
    }
    improve = {
        "summary": {
            "median_expectancy_eur": 5.0,
            "panel_net_eur": 400.0,
            "median_trades": 4.0,
            "n_exp_gt_0": 5,
        }
    }
    d = deltas_vs_core_baseline(baseline, improve)
    assert d["compare_to"] == CORE_BASELINE_ID
    assert d["improve_id"] == CORE_IMPROVE_ID
    assert abs(d["panel_net_eur"]["delta"] - (400.0 - 363.9983)) < 1e-6
    assert d["n_exp_gt_0"]["delta"] == 3
    assert d["promote_as_better"] is True

    worse = {
        "summary": {
            "median_expectancy_eur": 1.0,
            "panel_net_eur": 200.0,
            "median_trades": 3.0,
            "n_exp_gt_0": 5,
        }
    }
    d2 = deltas_vs_core_baseline(baseline, worse)
    assert d2["promote_as_better"] is False


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
    assert soft["n_expectancy_gt_0"] == 6
