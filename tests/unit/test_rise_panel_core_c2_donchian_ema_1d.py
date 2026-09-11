"""Unit tests: rise_panel Core C2 Donchian 40/20 + EMA50/200 lock + soft-promote deltas."""

from __future__ import annotations

import pytest

from atlas.paper.cascade import CORE_START_EUR
from atlas.paper.rise_panel import BASELINE_ID, PANEL_LABEL, RISE_PANEL_V1
from atlas.paper.rise_panel_core_c2_donchian_ema_1d_eval import (
    CORE_C0_ID,
    CORE_C1_ID,
    CORE_C2_ID,
    CORE_EMA_SNAPSHOT_54,
    deltas_vs_core_c0,
)
from atlas.strategy.core_doge_donchian40_20_ema50_200_1d import (
    BAR,
    EMA_FAST,
    EMA_SLOW,
    ENTRY_LOOKBACK,
    EXIT_LOOKBACK,
    FAMILY,
    FLAT,
    LADDER_ID,
    LONG,
    SLEEVE,
    CoreDogeDonchian4020Ema502001dParams,
    CoreDogeDonchian4020Ema502001dV1,
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
    assert CORE_C0_ID == BASELINE_ID
    assert CORE_C0_ID == "rise_panel_v1_core_doge_ema12_30_1d_eur140"
    assert CORE_C1_ID == "rise_panel_v1_core_doge_donchian40_20_1d_eur140"
    assert CORE_C2_ID == "rise_panel_v1_core_doge_donchian40_20_ema50_200_1d_eur140"
    assert CORE_START_EUR == 140.0
    assert PANEL_LABEL == "rise_panel_v1"
    assert len(RISE_PANEL_V1) == 7
    assert abs(CORE_EMA_SNAPSHOT_54["panel_net_eur"] - 363.9983) < 1e-4
    assert LADDER_ID == "C2"


def test_family_donchian40_20_ema50_200_locked():
    assert FAMILY == "donchian40_20_ema50_200_regime_1d"
    assert BAR == "1D"
    assert ENTRY_LOOKBACK == 40
    assert EXIT_LOOKBACK == 20
    assert EMA_FAST == 50
    assert EMA_SLOW == 200
    assert SLEEVE == "core"
    s = CoreDogeDonchian4020Ema502001dV1()
    assert "core_doge_donchian40_20_ema50_200_1d" in s.label
    assert s.warmup_bars() == max(EMA_SLOW, ENTRY_LOOKBACK + 1, EXIT_LOOKBACK + 1)


def test_rejects_lookback_ema_tf_sleeve_sweeps():
    with pytest.raises(ValueError, match="lookback"):
        CoreDogeDonchian4020Ema502001dV1(
            CoreDogeDonchian4020Ema502001dParams(entry_lookback=20)
        )
    with pytest.raises(ValueError, match="lookback"):
        CoreDogeDonchian4020Ema502001dV1(
            CoreDogeDonchian4020Ema502001dParams(exit_lookback=10)
        )
    with pytest.raises(ValueError, match="EMA"):
        CoreDogeDonchian4020Ema502001dV1(
            CoreDogeDonchian4020Ema502001dParams(ema_fast=12)
        )
    with pytest.raises(ValueError, match="EMA"):
        CoreDogeDonchian4020Ema502001dV1(
            CoreDogeDonchian4020Ema502001dParams(ema_slow=100)
        )
    with pytest.raises(ValueError, match="bar"):
        CoreDogeDonchian4020Ema502001dV1(CoreDogeDonchian4020Ema502001dParams(bar="4H"))
    with pytest.raises(ValueError, match="sleeve"):
        CoreDogeDonchian4020Ema502001dV1(CoreDogeDonchian4020Ema502001dParams(sleeve="mid"))


def test_force_flat_when_ema_regime_fails():
    """Strong uptrend seeds EMA50>EMA200 then dump forces flat via regime."""
    # Rising closes to seed bullish EMA50/200, then breakout, then crash.
    closes = [1.0 + 0.01 * i for i in range(220)]
    bars = [_bar(i, c, h=c + 0.05, lo=c - 0.05) for i, c in enumerate(closes)]
    # Breakout bar above prior 40-high
    last = closes[-1]
    bars.append(_bar(220, last + 0.5, h=last + 0.6, lo=last + 0.4))
    strat = CoreDogeDonchian4020Ema502001dV1()
    assert strat.desired_state(bars) == LONG
    # Crash: many bars down — EMA50 will eventually <= EMA200 or Donchian exit
    crash_start = last + 0.5
    for j in range(1, 80):
        c = crash_start - 0.05 * j
        bars.append(_bar(220 + j, c, h=c + 0.02, lo=c - 0.02))
    assert strat.desired_state(bars) == FLAT


def test_no_long_when_ema_bear():
    """Declining series: EMA50 <= EMA200 → stay flat even on local breakouts."""
    closes = [10.0 - 0.01 * i for i in range(220)]
    bars = [_bar(i, c, h=c + 0.05, lo=c - 0.05) for i, c in enumerate(closes)]
    # Local spike that would break prior 40-high of the declining series
    spike = closes[-1] + 1.0
    bars.append(_bar(220, spike, h=spike + 0.1, lo=spike - 0.1))
    strat = CoreDogeDonchian4020Ema502001dV1()
    assert strat.desired_state(bars) == FLAT


def test_never_short():
    closes = [1.0 + 0.005 * i for i in range(250)]
    bars = [_bar(i, c, h=c + 0.05, lo=c - 0.05) for i, c in enumerate(closes)]
    strat = CoreDogeDonchian4020Ema502001dV1()
    for i in range(200, len(bars)):
        assert strat.desired_state(bars[: i + 1]) in (LONG, FLAT)


def test_deltas_pass_but_worse():
    baseline = {
        "summary": {
            "median_expectancy_eur": -2.9545,
            "panel_net_eur": 363.9983,
            "median_trades": 1.0,
            "n_exp_gt_0": 2,
        },
        "soft_promote": {"verdict": "FAIL"},
    }
    improve = {
        "summary": {
            "median_expectancy_eur": 1.0,
            "panel_net_eur": 200.0,
            "median_trades": 2.0,
            "n_exp_gt_0": 5,
        },
        "soft_promote": {"verdict": "PASS", "pass": True},
    }
    d = deltas_vs_core_c0(baseline, improve)
    assert d["honesty_label"] == "PASS-but-worse"
    assert d["promote_as_better"] is False
    assert d["c3_allowed"] is True
    assert d["soft_pass_ne_arm"] is True


def test_deltas_fail_stops_c3():
    baseline = {
        "summary": {
            "median_expectancy_eur": -2.9545,
            "panel_net_eur": 363.9983,
            "median_trades": 1.0,
            "n_exp_gt_0": 2,
        },
    }
    improve = {
        "summary": {
            "median_expectancy_eur": -5.0,
            "panel_net_eur": 100.0,
            "median_trades": 1.0,
            "n_exp_gt_0": 2,
        },
        "soft_promote": {"verdict": "FAIL"},
    }
    d = deltas_vs_core_c0(baseline, improve)
    assert d["honesty_label"] == "FAIL"
    assert d["c3_allowed"] is False
    assert d["promote_as_better"] is False
