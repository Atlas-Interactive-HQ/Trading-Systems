"""Unit tests: rise_panel Scalp #62 BreakoutV1 1H lock + soft-promote deltas."""

from __future__ import annotations

import pytest

from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.rise_panel import (
    PANEL_LABEL,
    RISE_PANEL_V1,
    soft_promote_score,
)
from atlas.paper.rise_panel_scalp_breakout_1h_eval import (
    SCALP_4H_ID,
    SCALP_DONCHIAN_ID,
    SCALP_IMPROVE_ID,
    SCALP_PROVISIONAL_ID,
    SCALP_RSI_MR_ID,
    deltas_vs_ref,
)
from atlas.strategy.scalp_doge_breakout_1h import (
    ATR_PERIOD,
    BAR,
    FAMILY,
    FLAT,
    LONG,
    LOOKBACK,
    MIN_ATR_FRAC,
    SLEEVE,
    ScalpDogeBreakout1hParams,
    ScalpDogeBreakout1hV1,
)
from atlas.paper.types import Bar

BAR_MS = 60 * 60 * 1000
START = 1_600_000_000_000
SYM = "DOGE-USDT"


def _bar(i: int, c: float, h: float | None = None, lo: float | None = None) -> Bar:
    ts = START + i * BAR_MS
    hi = h if h is not None else c + 0.01
    low = lo if lo is not None else c - 0.01
    return Bar(SYM, ts, ts + BAR_MS, c, hi, low, c, 1.0, True, "test")


def test_ids_and_sleeve_locked():
    assert SCALP_PROVISIONAL_ID == "rise_panel_v1_scalp_doge_ema12_30_1h_daily_bull_eur20"
    assert SCALP_4H_ID == "rise_panel_v1_scalp_doge_ema12_30_4h_eur20"
    assert SCALP_DONCHIAN_ID == "rise_panel_v1_scalp_doge_donchian20_10_1h_eur20"
    assert SCALP_RSI_MR_ID == "rise_panel_v1_scalp_doge_rsi14_mr_1h_eur20"
    assert SCALP_IMPROVE_ID == "rise_panel_v1_scalp_doge_breakoutv1_1h_eur20"
    assert SCALP_START_EUR == 20.0
    assert PANEL_LABEL == "rise_panel_v1"
    assert len(RISE_PANEL_V1) == 7


def test_family_breakout_locked():
    assert FAMILY == "breakout_v1_long_flat_1h"
    assert BAR == "1H"
    assert LOOKBACK == 16
    assert ATR_PERIOD == 14
    assert MIN_ATR_FRAC == 0.001
    assert SLEEVE == "scalp"
    s = ScalpDogeBreakout1hV1()
    assert "scalp_doge_breakout_1h" in s.label
    assert s.warmup_bars() == max(LOOKBACK, ATR_PERIOD) + 1
    assert s.params.oneh_filter == "off"


def test_rejects_lookback_tf_sleeve_sweeps():
    with pytest.raises(ValueError, match="lookback"):
        ScalpDogeBreakout1hV1(ScalpDogeBreakout1hParams(lookback=20))
    with pytest.raises(ValueError, match="atr_period"):
        ScalpDogeBreakout1hV1(ScalpDogeBreakout1hParams(atr_period=10))
    with pytest.raises(ValueError, match="bar"):
        ScalpDogeBreakout1hV1(ScalpDogeBreakout1hParams(bar="15m"))
    with pytest.raises(ValueError, match="sleeve"):
        ScalpDogeBreakout1hV1(ScalpDogeBreakout1hParams(sleeve="mid"))
    with pytest.raises(ValueError, match="oneh_filter"):
        ScalpDogeBreakout1hV1(ScalpDogeBreakout1hParams(oneh_filter="stub"))


def test_entry_break_above_16_exit_below_16():
    """BreakoutV1 channel: break prior 16-high → long; break prior 16-low → flat."""
    bars = [_bar(i, 100.0, h=100.5, lo=99.5) for i in range(16)]
    # Need ATR history too — widen ranges so ATR/close is fine
    bars = [_bar(i, 100.0 + 0.01 * (i % 3), h=101.0, lo=99.0) for i in range(20)]
    bars.append(_bar(20, 102.0, h=102.5, lo=100.0))  # close > prior highs
    strat = ScalpDogeBreakout1hV1()
    assert strat.desired_state(bars) == LONG
    bars.append(_bar(21, 50.0, h=102.0, lo=49.0))
    assert strat.desired_state(bars) == FLAT


def test_never_short_and_no_daily_bull_attr():
    closes = [1.0 + 0.01 * i for i in range(80)]
    bars = [_bar(i, c, h=c + 0.05, lo=c - 0.05) for i, c in enumerate(closes)]
    strat = ScalpDogeBreakout1hV1()
    for i in range(len(bars)):
        assert strat.desired_state(bars[: i + 1]) in (LONG, FLAT)
    assert not hasattr(strat, "set_daily_bars")


def test_deltas_vs_ref_shape():
    provisional = {
        "summary": {
            "median_expectancy_eur": 0.2,
            "panel_net_eur": 44.7,
            "median_trades": 18.0,
            "n_exp_gt_0": 4,
        }
    }
    improve = {
        "summary": {
            "median_expectancy_eur": 0.05,
            "panel_net_eur": 30.0,
            "median_trades": 12.0,
            "n_exp_gt_0": 3,
        }
    }
    d = deltas_vs_ref(
        provisional, improve, ref_id=SCALP_PROVISIONAL_ID, improve_id=SCALP_IMPROVE_ID
    )
    assert d["compare_to"] == SCALP_PROVISIONAL_ID
    assert d["improve_id"] == SCALP_IMPROVE_ID
    assert abs(d["median_expectancy_eur"]["delta"] - (0.05 - 0.2)) < 1e-9
    assert abs(d["panel_net_eur"]["delta"] - (30.0 - 44.7)) < 1e-9
    assert d["median_trades"]["delta"] == -6.0
    assert d["n_exp_gt_0"]["delta"] == -1
    assert d["not_a_forecast"] is True
    assert d["place_orders"] is False


def test_soft_promote_still_gates_improve_rows():
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
    assert sc["pass"] is True
    assert sc["n_expectancy_gt_0"] == 6
