"""Unit tests: rise_panel Core C1 Donchian 40/20 1D lock + soft-promote deltas."""

from __future__ import annotations

import pytest

from atlas.paper.cascade import CORE_START_EUR
from atlas.paper.rise_panel import BASELINE_ID, PANEL_LABEL, RISE_PANEL_V1
from atlas.paper.rise_panel_core_c1_donchian_1d_eval import (
    CORE_C0_ID,
    CORE_C1_ID,
    CORE_EMA_SNAPSHOT_54,
    deltas_vs_core_c0,
)
from atlas.strategy.core_doge_donchian40_20_1d import (
    BAR,
    ENTRY_LOOKBACK,
    EXIT_LOOKBACK,
    FAMILY,
    FLAT,
    LADDER_ID,
    LONG,
    SLEEVE,
    CoreDogeDonchian40201dParams,
    CoreDogeDonchian40201dV1,
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
    assert CORE_START_EUR == 140.0
    assert PANEL_LABEL == "rise_panel_v1"
    assert len(RISE_PANEL_V1) == 7
    assert abs(CORE_EMA_SNAPSHOT_54["panel_net_eur"] - 363.9983) < 1e-4
    assert LADDER_ID == "C1"


def test_family_donchian40_20_locked():
    assert FAMILY == "donchian40_20_long_flat_1d"
    assert BAR == "1D"
    assert ENTRY_LOOKBACK == 40
    assert EXIT_LOOKBACK == 20
    assert SLEEVE == "core"
    s = CoreDogeDonchian40201dV1()
    assert "core_doge_donchian40_20_1d" in s.label
    assert s.warmup_bars() == max(ENTRY_LOOKBACK, EXIT_LOOKBACK) + 1


def test_rejects_lookback_tf_sleeve_sweeps():
    with pytest.raises(ValueError, match="lookback"):
        CoreDogeDonchian40201dV1(CoreDogeDonchian40201dParams(entry_lookback=20))
    with pytest.raises(ValueError, match="lookback"):
        CoreDogeDonchian40201dV1(CoreDogeDonchian40201dParams(exit_lookback=10))
    with pytest.raises(ValueError, match="bar"):
        CoreDogeDonchian40201dV1(CoreDogeDonchian40201dParams(bar="4H"))
    with pytest.raises(ValueError, match="sleeve"):
        CoreDogeDonchian40201dV1(CoreDogeDonchian40201dParams(sleeve="mid"))


def test_entry_break_above_40_exit_below_20():
    """C1 Donchian: break prior 40-high → long; break prior 20-low → flat."""
    bars = [_bar(i, 100.0 + 0.01 * (i % 3), h=101.0, lo=99.0) for i in range(45)]
    bars.append(_bar(45, 102.0, h=102.5, lo=100.0))  # close > prior 40-high
    strat = CoreDogeDonchian40201dV1()
    assert strat.desired_state(bars) == LONG
    bars.append(_bar(46, 101.5, h=102.0, lo=100.5))
    assert strat.desired_state(bars) == LONG
    bars.append(_bar(47, 50.0, h=101.0, lo=49.0))  # close < prior 20-low
    assert strat.desired_state(bars) == FLAT


def test_never_short():
    closes = [1.0 + 0.01 * i for i in range(100)]
    bars = [_bar(i, c, h=c + 0.05, lo=c - 0.05) for i, c in enumerate(closes)]
    strat = CoreDogeDonchian40201dV1()
    for i in range(len(bars)):
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
    assert d["c2_allowed"] is True
    assert d["soft_pass_ne_arm"] is True


def test_deltas_fail_eliminates_c2():
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
    assert d["c2_allowed"] is False
    assert d["promote_as_better"] is False
