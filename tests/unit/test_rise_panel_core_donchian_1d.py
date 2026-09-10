"""Unit tests: rise_panel Core #70 Donchian 20/10 1D lock + soft-promote deltas."""

from __future__ import annotations

import pytest

from atlas.paper.cascade import CORE_START_EUR, MID_START_EUR
from atlas.paper.rise_panel import (
    BASELINE_ID,
    PANEL_LABEL,
    RISE_PANEL_V1,
    soft_promote_score,
)
from atlas.paper.rise_panel_core_donchian_1d_eval import (
    CORE_BASELINE_ID,
    CORE_EMA_SNAPSHOT_54,
    CORE_IMPROVE_ID,
    CORE_MID_BOOK_EUR,
    CORE_MID_BOOK_ID,
    MID_BREAKOUT_SNAPSHOT_65,
    deltas_vs_core_baseline,
)
from atlas.strategy.core_doge_donchian_1d import (
    BAR,
    ENTRY_LOOKBACK,
    EXIT_LOOKBACK,
    FAMILY,
    FLAT,
    LONG,
    SLEEVE,
    CoreDogeDonchian1dParams,
    CoreDogeDonchian1dV1,
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
    assert CORE_IMPROVE_ID == "rise_panel_v1_core_doge_donchian20_10_1d_eur140"
    assert CORE_START_EUR == 140.0
    assert MID_START_EUR == 40.0
    assert CORE_MID_BOOK_EUR == 180.0
    assert CORE_MID_BOOK_ID == "rise_panel_v1_core_mid_book_180_core_donchian20_10_1d"
    assert PANEL_LABEL == "rise_panel_v1"
    assert len(RISE_PANEL_V1) == 7
    # measured Core EMA snapshot — do not invent
    assert abs(CORE_EMA_SNAPSHOT_54["panel_net_eur"] - 363.9983) < 1e-4
    assert abs(MID_BREAKOUT_SNAPSHOT_65["panel_net_eur"] - 95.4483) < 1e-4


def test_family_donchian_locked():
    assert FAMILY == "donchian20_10_long_flat_1d"
    assert BAR == "1D"
    assert ENTRY_LOOKBACK == 20
    assert EXIT_LOOKBACK == 10
    assert SLEEVE == "core"
    s = CoreDogeDonchian1dV1()
    assert "core_doge_donchian_1d" in s.label
    assert s.warmup_bars() == max(ENTRY_LOOKBACK, EXIT_LOOKBACK) + 1


def test_rejects_lookback_tf_sleeve_sweeps():
    with pytest.raises(ValueError, match="lookback"):
        CoreDogeDonchian1dV1(CoreDogeDonchian1dParams(entry_lookback=25))
    with pytest.raises(ValueError, match="lookback"):
        CoreDogeDonchian1dV1(CoreDogeDonchian1dParams(exit_lookback=5))
    with pytest.raises(ValueError, match="bar"):
        CoreDogeDonchian1dV1(CoreDogeDonchian1dParams(bar="4H"))
    with pytest.raises(ValueError, match="sleeve"):
        CoreDogeDonchian1dV1(CoreDogeDonchian1dParams(sleeve="mid"))


def test_entry_break_above_20_exit_below_10():
    """Canonical Donchian: break prior 20-high → long; break prior 10-low → flat."""
    bars = [_bar(i, 100.0 + 0.01 * (i % 3), h=101.0, lo=99.0) for i in range(25)]
    bars.append(_bar(25, 102.0, h=102.5, lo=100.0))  # close > prior 20-high
    strat = CoreDogeDonchian1dV1()
    assert strat.desired_state(bars) == LONG
    # stay long while above exit channel
    bars.append(_bar(26, 101.5, h=102.0, lo=100.5))
    assert strat.desired_state(bars) == LONG
    # exit: close < prior 10-low
    bars.append(_bar(27, 50.0, h=101.0, lo=49.0))
    assert strat.desired_state(bars) == FLAT


def test_never_short_and_no_ema_filter_attr():
    closes = [1.0 + 0.01 * i for i in range(80)]
    bars = [_bar(i, c, h=c + 0.05, lo=c - 0.05) for i, c in enumerate(closes)]
    strat = CoreDogeDonchian1dV1()
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
        {"ok": True, "n_trades": 7, "expectancy_after_costs_eur": 0.3, "net_return_eur": 1.5},
        {"ok": True, "n_trades": 2, "expectancy_after_costs_eur": -0.1, "net_return_eur": -0.2},
        {"ok": True, "n_trades": 4, "expectancy_after_costs_eur": 0.4, "net_return_eur": 1.2},
    ]
    soft = soft_promote_score(rows)
    assert soft["verdict"] == "PASS"
