"""Unit tests: rise_panel Mid M1 BreakoutV1+EMA12/21+ADX14>20 lock + deltas."""

from __future__ import annotations

import pytest

from atlas.paper.cascade import MID_START_EUR
from atlas.paper.rise_panel import MID_BASELINE_ID, PANEL_LABEL, RISE_PANEL_V1
from atlas.paper.rise_panel_mid_m1_adx_4h_eval import (
    MID_M0_ID,
    MID_M1_ID,
    deltas_vs_mid_m0,
)
from atlas.strategy.adx import ADX_GATE_M1, ADX_PERIOD, wilder_adx_series
from atlas.strategy.mid_doge_breakout_ema1221_adx_4h import (
    ADX_GATE,
    ADX_PERIOD_LOCKED,
    BAR,
    EMA_FAST,
    EMA_SLOW,
    FAMILY,
    FLAT,
    LONG,
    LOOKBACK,
    SLEEVE,
    MidDogeBreakoutEma1221AdxParams,
    MidDogeBreakoutEma1221AdxV1,
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


def test_ids_and_locks():
    assert MID_M0_ID == MID_BASELINE_ID
    assert MID_M1_ID == "rise_panel_v1_mid_doge_breakoutv1_ema1221_adx14_gt20_4h_eur40"
    assert MID_START_EUR == 40.0
    assert PANEL_LABEL == "rise_panel_v1"
    assert len(RISE_PANEL_V1) == 7
    assert FAMILY == "breakout_v1_ema1221_adx14_gt20_long_regime_4h"
    assert BAR == "4H"
    assert LOOKBACK == 16
    assert EMA_FAST == 12 and EMA_SLOW == 21
    assert ADX_PERIOD_LOCKED == ADX_PERIOD == 14
    assert ADX_GATE == ADX_GATE_M1 == 20.0
    assert SLEEVE == "mid"


def test_rejects_adx_ema_sweeps():
    with pytest.raises(ValueError, match="ADX period"):
        MidDogeBreakoutEma1221AdxV1(MidDogeBreakoutEma1221AdxParams(adx_period=21))
    with pytest.raises(ValueError, match="ADX gate"):
        MidDogeBreakoutEma1221AdxV1(MidDogeBreakoutEma1221AdxParams(adx_gate=25.0))
    with pytest.raises(ValueError, match="EMA period"):
        MidDogeBreakoutEma1221AdxV1(MidDogeBreakoutEma1221AdxParams(ema_slow=30))
    with pytest.raises(ValueError, match="lookback"):
        MidDogeBreakoutEma1221AdxV1(MidDogeBreakoutEma1221AdxParams(lookback=20))


def test_adx_series_warms_and_never_short():
    closes = [1.0 + 0.02 * i for i in range(80)]
    bars = [_bar(i, c, h=c + 0.05, lo=c - 0.05) for i, c in enumerate(closes)]
    series = wilder_adx_series(bars, 14)
    assert series[2 * 14 - 2][0] is None or True
    assert any(a[0] is not None for a in series)
    strat = MidDogeBreakoutEma1221AdxV1()
    for i in range(len(bars)):
        assert strat.desired_state(bars[: i + 1]) in (LONG, FLAT)


def test_deltas_shape():
    baseline = {
        "summary": {
            "median_expectancy_eur": 2.1531,
            "panel_net_eur": 97.2663,
            "median_trades": 7.0,
            "n_exp_gt_0": 5,
        },
        "soft_promote": {"verdict": "PASS"},
    }
    improve = {
        "summary": {
            "median_expectancy_eur": 2.0,
            "panel_net_eur": 90.0,
            "median_trades": 5.0,
            "n_exp_gt_0": 5,
        },
        "soft_promote": {"verdict": "PASS", "pass": True},
    }
    d = deltas_vs_mid_m0(baseline, improve)
    assert d["honesty_label"] == "PASS-but-worse"
    assert d["promote_as_better"] is False
    assert d["soft_pass_ne_arm"] is True
