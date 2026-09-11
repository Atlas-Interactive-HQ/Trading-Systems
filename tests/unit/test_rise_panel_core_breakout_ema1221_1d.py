"""Unit tests: rise_panel Core #73 BreakoutV1 + EMA12/21 1D lock + deltas."""

from __future__ import annotations

import pytest

from atlas.paper.cascade import CORE_START_EUR, MID_START_EUR
from atlas.paper.rise_panel import (
    BASELINE_ID,
    MID_BASELINE_ID,
    PANEL_LABEL,
    RISE_PANEL_V1,
    soft_promote_score,
)
from atlas.paper.rise_panel_core_breakout_ema1221_1d_eval import (
    CORE_BASELINE_ID,
    CORE_EMA_SNAPSHOT_54,
    CORE_IMPROVE_ID,
    CORE_MID_BOOK_EUR,
    CORE_MID_BOOK_ID,
    MID_71_SNAPSHOT,
    deltas_vs_core_baseline,
)
from atlas.strategy.core_doge_breakout_ema1221_1d import (
    ATR_PERIOD,
    BAR,
    EMA_FAST,
    EMA_SLOW,
    FAMILY,
    FLAT,
    LONG,
    LOOKBACK,
    MIN_ATR_FRAC,
    SLEEVE,
    CoreDogeBreakoutEma1221Params,
    CoreDogeBreakoutEma1221V1,
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
    assert CORE_IMPROVE_ID == "rise_panel_v1_core_doge_breakoutv1_ema1221_long_1d_eur140"
    assert CORE_START_EUR == 140.0
    assert MID_START_EUR == 40.0
    assert CORE_MID_BOOK_EUR == 180.0
    assert CORE_MID_BOOK_ID == "rise_panel_v1_core_mid_book_180_core_breakout_ema1221_1d"
    assert PANEL_LABEL == "rise_panel_v1"
    assert len(RISE_PANEL_V1) == 7
    assert abs(CORE_EMA_SNAPSHOT_54["panel_net_eur"] - 363.9983) < 1e-4
    assert abs(MID_71_SNAPSHOT["panel_net_eur"] - 97.2663) < 1e-4
    assert MID_BASELINE_ID == "rise_panel_v1_mid_doge_breakoutv1_ema1221_long_4h_eur40"


def test_family_breakout_ema1221_locked():
    assert FAMILY == "breakout_v1_ema1221_long_regime_1d"
    assert BAR == "1D"
    assert LOOKBACK == 16
    assert ATR_PERIOD == 14
    assert MIN_ATR_FRAC == 0.001
    assert EMA_FAST == 12
    assert EMA_SLOW == 21
    assert SLEEVE == "core"
    s = CoreDogeBreakoutEma1221V1()
    assert "core_doge_breakout_ema1221_1d" in s.label
    assert s.warmup_bars() >= max(LOOKBACK, ATR_PERIOD, EMA_SLOW) + 1
    assert s.params.oneh_filter == "off"


def test_rejects_lookback_ema_tf_sleeve_sweeps():
    with pytest.raises(ValueError, match="lookback"):
        CoreDogeBreakoutEma1221V1(CoreDogeBreakoutEma1221Params(lookback=20))
    with pytest.raises(ValueError, match="EMA period"):
        CoreDogeBreakoutEma1221V1(CoreDogeBreakoutEma1221Params(ema_fast=12, ema_slow=30))
    with pytest.raises(ValueError, match="bar"):
        CoreDogeBreakoutEma1221V1(CoreDogeBreakoutEma1221Params(bar="4H"))
    with pytest.raises(ValueError, match="sleeve"):
        CoreDogeBreakoutEma1221V1(CoreDogeBreakoutEma1221Params(sleeve="mid"))
    with pytest.raises(ValueError, match="oneh_filter"):
        CoreDogeBreakoutEma1221V1(CoreDogeBreakoutEma1221Params(oneh_filter="stub"))


def test_ema_regime_and_never_short():
    closes = [100.0 + 0.01 * (i % 3) for i in range(40)]
    closes += [closes[-1] + i * 0.5 for i in range(1, 40)]
    bars = [_bar(i, c, h=c + 0.2, lo=c - 0.2) for i, c in enumerate(closes)]
    strat = CoreDogeBreakoutEma1221V1()
    states = [strat.desired_state(bars[: i + 1]) for i in range(len(bars))]
    assert all(st in (LONG, FLAT) for st in states)
    assert LONG in states


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
