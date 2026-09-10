"""Unit tests: rise_panel Mid #65 BreakoutV1 4H lock + soft-promote deltas."""

from __future__ import annotations

import pytest

from atlas.paper.cascade import CORE_START_EUR, MID_START_EUR
from atlas.paper.rise_panel import (
    MID_CANDIDATE_ID,
    PANEL_LABEL,
    RISE_PANEL_V1,
    soft_promote_score,
)
from atlas.paper.rise_panel_mid_breakout_4h_eval import (
    CORE_MID_BOOK_EUR,
    CORE_MID_BOOK_ID,
    MID_BASELINE_ID,
    MID_DONCHIAN_64_ID,
    MID_IMPROVE_ID,
    deltas_vs_donchian_64,
    deltas_vs_mid_baseline,
)
from atlas.strategy.mid_doge_breakout_4h import (
    ATR_PERIOD,
    BAR,
    FAMILY,
    FLAT,
    LONG,
    LOOKBACK,
    MIN_ATR_FRAC,
    SLEEVE,
    MidDogeBreakout4hParams,
    MidDogeBreakout4hV1,
)
from atlas.paper.types import Bar

BAR_MS = 4 * 60 * 60 * 1000
START = 1_600_000_000_000
SYM = "DOGE-USDT"


def _bar(i: int, c: float, h: float | None = None, lo: float | None = None) -> Bar:
    ts = START + i * BAR_MS
    hi = h if h is not None else c + 0.01
    low = lo if lo is not None else c - 0.01
    return Bar(SYM, ts, ts + BAR_MS, c, hi, low, c, 1.0, True, "test")


def test_ids_and_sleeve_locked():
    assert MID_BASELINE_ID == MID_CANDIDATE_ID
    assert MID_BASELINE_ID == "rise_panel_v1_mid_doge_ema12_30_4h_eur40"
    assert MID_IMPROVE_ID == "rise_panel_v1_mid_doge_breakoutv1_4h_eur40"
    assert MID_DONCHIAN_64_ID == "rise_panel_v1_mid_doge_donchian20_10_4h_eur40"
    assert MID_START_EUR == 40.0
    assert CORE_START_EUR == 140.0
    assert CORE_MID_BOOK_EUR == 180.0
    assert CORE_MID_BOOK_ID == "rise_panel_v1_core_mid_book_180_mid_breakoutv1_4h"
    assert PANEL_LABEL == "rise_panel_v1"
    assert len(RISE_PANEL_V1) == 7


def test_family_breakout_locked():
    assert FAMILY == "breakout_v1_long_flat_4h"
    assert BAR == "4H"
    assert LOOKBACK == 16
    assert ATR_PERIOD == 14
    assert MIN_ATR_FRAC == 0.001
    assert SLEEVE == "mid"
    s = MidDogeBreakout4hV1()
    assert "mid_doge_breakout_4h" in s.label
    assert s.warmup_bars() == max(LOOKBACK, ATR_PERIOD) + 1
    assert s.params.oneh_filter == "off"


def test_rejects_lookback_tf_sleeve_sweeps():
    with pytest.raises(ValueError, match="lookback"):
        MidDogeBreakout4hV1(MidDogeBreakout4hParams(lookback=20))
    with pytest.raises(ValueError, match="atr_period"):
        MidDogeBreakout4hV1(MidDogeBreakout4hParams(atr_period=10))
    with pytest.raises(ValueError, match="bar"):
        MidDogeBreakout4hV1(MidDogeBreakout4hParams(bar="1H"))
    with pytest.raises(ValueError, match="sleeve"):
        MidDogeBreakout4hV1(MidDogeBreakout4hParams(sleeve="scalp"))
    with pytest.raises(ValueError, match="oneh_filter"):
        MidDogeBreakout4hV1(MidDogeBreakout4hParams(oneh_filter="stub"))


def test_entry_break_above_16_exit_below_16():
    """BreakoutV1 channel: break prior 16-high → long; break prior 16-low → flat."""
    bars = [_bar(i, 100.0 + 0.01 * (i % 3), h=101.0, lo=99.0) for i in range(20)]
    bars.append(_bar(20, 102.0, h=102.5, lo=100.0))  # close > prior highs
    strat = MidDogeBreakout4hV1()
    assert strat.desired_state(bars) == LONG
    bars.append(_bar(21, 50.0, h=102.0, lo=49.0))
    assert strat.desired_state(bars) == FLAT


def test_never_short_and_no_ema_filter_attr():
    closes = [1.0 + 0.01 * i for i in range(80)]
    bars = [_bar(i, c, h=c + 0.05, lo=c - 0.05) for i, c in enumerate(closes)]
    strat = MidDogeBreakout4hV1()
    for i in range(len(bars)):
        assert strat.desired_state(bars[: i + 1]) in (LONG, FLAT)
    assert not hasattr(strat, "set_daily_bars")
    assert not hasattr(strat, "ema_filter")


def test_deltas_vs_mid_baseline_shape():
    baseline = {
        "summary": {
            "median_expectancy_eur": 2.0928,
            "panel_net_eur": 83.6104,
            "median_trades": 7.0,
            "n_exp_gt_0": 6,
        }
    }
    improve = {
        "summary": {
            "median_expectancy_eur": 1.0,
            "panel_net_eur": 50.0,
            "median_trades": 9.0,
            "n_exp_gt_0": 5,
        }
    }
    d = deltas_vs_mid_baseline(baseline, improve)
    assert d["compare_to"] == MID_BASELINE_ID
    assert d["improve_id"] == MID_IMPROVE_ID
    assert abs(d["panel_net_eur"]["delta"] - (50.0 - 83.6104)) < 1e-6
    assert d["n_exp_gt_0"]["delta"] == -1


def test_deltas_vs_donchian_64_shape():
    improve = {
        "summary": {
            "median_expectancy_eur": 1.0,
            "panel_net_eur": 50.0,
            "median_trades": 9.0,
            "n_exp_gt_0": 5,
        }
    }
    d = deltas_vs_donchian_64(improve)
    assert d["compare_to"] == MID_DONCHIAN_64_ID
    assert d["improve_id"] == MID_IMPROVE_ID
    assert abs(d["panel_net_eur"]["delta"] - (50.0 - 83.1242)) < 1e-6
    assert d["n_exp_gt_0"]["delta"] == 0


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
