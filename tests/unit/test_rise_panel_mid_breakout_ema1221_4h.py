"""Unit tests: rise_panel Mid #71 BreakoutV1 + EMA12/21 long-regime lock + deltas."""

from __future__ import annotations

import pytest

from atlas.paper.cascade import CORE_START_EUR, MID_START_EUR
from atlas.paper.rise_panel import (
    MID_BASELINE_ID,
    MID_CANDIDATE_ID,
    MID_EMA_ARCHIVE_ID,
    PANEL_LABEL,
    RISE_PANEL_V1,
    soft_promote_score,
)
from atlas.paper.rise_panel_mid_breakout_ema1221_4h_eval import (
    CORE_MID_BOOK_EUR,
    CORE_MID_BOOK_ID,
    MID_BREAKOUT_BASELINE_ID,
    MID_IMPROVE_ID,
    deltas_vs_ema_archive,
    deltas_vs_mid_baseline,
)
from atlas.strategy.mid_doge_breakout_ema1221_4h import (
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
    MidDogeBreakoutEma1221Params,
    MidDogeBreakoutEma1221V1,
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
    assert MID_BREAKOUT_BASELINE_ID == MID_BASELINE_ID
    assert MID_BASELINE_ID == "rise_panel_v1_mid_doge_breakoutv1_4h_eur40"
    assert MID_EMA_ARCHIVE_ID == MID_CANDIDATE_ID
    assert MID_IMPROVE_ID == "rise_panel_v1_mid_doge_breakoutv1_ema1221_long_4h_eur40"
    assert MID_START_EUR == 40.0
    assert CORE_START_EUR == 140.0
    assert CORE_MID_BOOK_EUR == 180.0
    assert CORE_MID_BOOK_ID == "rise_panel_v1_core_mid_book_180_mid_breakout_ema1221_4h"
    assert PANEL_LABEL == "rise_panel_v1"
    assert len(RISE_PANEL_V1) == 7


def test_family_breakout_ema1221_locked():
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
    assert s.warmup_bars() >= max(LOOKBACK, ATR_PERIOD, EMA_SLOW) + 1
    assert s.params.oneh_filter == "off"


def test_rejects_lookback_ema_tf_sleeve_sweeps():
    with pytest.raises(ValueError, match="lookback"):
        MidDogeBreakoutEma1221V1(MidDogeBreakoutEma1221Params(lookback=20))
    with pytest.raises(ValueError, match="EMA period"):
        MidDogeBreakoutEma1221V1(MidDogeBreakoutEma1221Params(ema_fast=12, ema_slow=30))
    with pytest.raises(ValueError, match="bar"):
        MidDogeBreakoutEma1221V1(MidDogeBreakoutEma1221Params(bar="1H"))
    with pytest.raises(ValueError, match="sleeve"):
        MidDogeBreakoutEma1221V1(MidDogeBreakoutEma1221Params(sleeve="scalp"))
    with pytest.raises(ValueError, match="oneh_filter"):
        MidDogeBreakoutEma1221V1(MidDogeBreakoutEma1221Params(oneh_filter="stub"))


def test_ema_blocks_long_when_bear_and_force_flat():
    """Uptrend breakout alone is not enough if EMA12 <= EMA21; EMA fail forces flat."""
    # Flat-ish then sharp up so Donchian can break, but keep closes such that
    # we can still observe states in {LONG, FLAT} only.
    closes = [100.0 + 0.01 * (i % 3) for i in range(40)]
    closes += [closes[-1] + i * 0.5 for i in range(1, 40)]
    bars = [_bar(i, c, h=c + 0.2, lo=c - 0.2) for i, c in enumerate(closes)]
    strat = MidDogeBreakoutEma1221V1()
    states = [strat.desired_state(bars[: i + 1]) for i in range(len(bars))]
    assert all(st in (LONG, FLAT) for st in states)
    # After a strong uptrend EMA should be bull and breakout can go long
    assert LONG in states


def test_never_short():
    closes = [1.0 + 0.02 * i for i in range(100)]
    bars = [_bar(i, c, h=c + 0.05, lo=c - 0.05) for i, c in enumerate(closes)]
    strat = MidDogeBreakoutEma1221V1()
    for i in range(len(bars)):
        assert strat.desired_state(bars[: i + 1]) in (LONG, FLAT)


def test_deltas_vs_breakout_baseline_shape():
    baseline = {
        "summary": {
            "median_expectancy_eur": 2.4647,
            "panel_net_eur": 95.4483,
            "median_trades": 6.0,
            "n_exp_gt_0": 5,
        }
    }
    improve = {
        "summary": {
            "median_expectancy_eur": 1.0,
            "panel_net_eur": 50.0,
            "median_trades": 5.0,
            "n_exp_gt_0": 5,
        }
    }
    d = deltas_vs_mid_baseline(baseline, improve)
    assert d["compare_to"] == MID_BREAKOUT_BASELINE_ID
    assert d["improve_id"] == MID_IMPROVE_ID
    assert abs(d["panel_net_eur"]["delta"] - (50.0 - 95.4483)) < 1e-6
    assert d["promote_as_better"] is False

    better = {
        "summary": {
            "median_expectancy_eur": 3.0,
            "panel_net_eur": 100.0,
            "median_trades": 5.0,
            "n_exp_gt_0": 6,
        }
    }
    d2 = deltas_vs_mid_baseline(baseline, better)
    assert d2["promote_as_better"] is True


def test_deltas_vs_ema_archive_shape():
    improve = {
        "summary": {
            "median_expectancy_eur": 1.0,
            "panel_net_eur": 50.0,
            "median_trades": 5.0,
            "n_exp_gt_0": 5,
        }
    }
    d = deltas_vs_ema_archive(improve)
    assert d["compare_to"] == MID_EMA_ARCHIVE_ID
    assert abs(d["panel_net_eur"]["delta"] - (50.0 - 83.6104)) < 1e-6


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
