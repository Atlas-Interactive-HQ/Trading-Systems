"""Unit tests: rise_panel Scalp #61 Donchian 20/10 1H lock + soft-promote deltas."""

from __future__ import annotations

import pytest

from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.rise_panel import (
    PANEL_LABEL,
    RISE_PANEL_V1,
    soft_promote_score,
)
from atlas.paper.rise_panel_scalp_donchian_1h_eval import (
    SCALP_4H_ID,
    SCALP_IMPROVE_ID,
    SCALP_PROVISIONAL_ID,
    SCALP_RSI_MR_ID,
    deltas_vs_ref,
)
from atlas.strategy.scalp_doge_donchian_1h import (
    BAR,
    ENTRY_LOOKBACK,
    EXIT_LOOKBACK,
    FAMILY,
    FLAT,
    LONG,
    SLEEVE,
    ScalpDogeDonchian1hParams,
    ScalpDogeDonchian1hV1,
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
    assert SCALP_RSI_MR_ID == "rise_panel_v1_scalp_doge_rsi14_mr_1h_eur20"
    assert SCALP_IMPROVE_ID == "rise_panel_v1_scalp_doge_donchian20_10_1h_eur20"
    assert SCALP_START_EUR == 20.0
    assert PANEL_LABEL == "rise_panel_v1"
    assert len(RISE_PANEL_V1) == 7


def test_family_donchian_locked():
    assert FAMILY == "donchian20_10_long_flat_1h"
    assert BAR == "1H"
    assert ENTRY_LOOKBACK == 20
    assert EXIT_LOOKBACK == 10
    assert SLEEVE == "scalp"
    s = ScalpDogeDonchian1hV1()
    assert "scalp_doge_donchian_1h" in s.label
    assert s.warmup_bars() == max(ENTRY_LOOKBACK, EXIT_LOOKBACK) + 1


def test_rejects_lookback_tf_sleeve_sweeps():
    with pytest.raises(ValueError, match="lookback"):
        ScalpDogeDonchian1hV1(ScalpDogeDonchian1hParams(entry_lookback=16))
    with pytest.raises(ValueError, match="lookback"):
        ScalpDogeDonchian1hV1(ScalpDogeDonchian1hParams(exit_lookback=5))
    with pytest.raises(ValueError, match="bar"):
        ScalpDogeDonchian1hV1(ScalpDogeDonchian1hParams(bar="15m"))
    with pytest.raises(ValueError, match="sleeve"):
        ScalpDogeDonchian1hV1(ScalpDogeDonchian1hParams(sleeve="mid"))


def test_entry_break_above_20_exit_below_10():
    """Canonical Donchian: break prior 20-high → long; break prior 10-low → flat."""
    # Flat channel then breakout
    bars = [_bar(i, 100.0, h=100.5, lo=99.5) for i in range(20)]
    bars.append(_bar(20, 101.0, h=101.5, lo=100.0))  # close > prior 100.5
    strat = ScalpDogeDonchian1hV1()
    assert strat.desired_state(bars) == LONG
    # Dump below prior 10-low
    bars.append(_bar(21, 50.0, h=101.0, lo=49.0))
    assert strat.desired_state(bars) == FLAT


def test_never_short():
    closes = [1.0 + 0.01 * i for i in range(80)]
    bars = [_bar(i, c) for i, c in enumerate(closes)]
    strat = ScalpDogeDonchian1hV1()
    for i in range(len(bars)):
        assert strat.desired_state(bars[: i + 1]) in (LONG, FLAT)


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
