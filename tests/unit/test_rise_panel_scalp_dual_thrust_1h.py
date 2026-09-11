"""Unit tests: rise_panel Scalp #83 Dual Thrust 1H lock + soft-promote deltas."""

from __future__ import annotations

import pytest

from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.rise_panel import (
    PANEL_LABEL,
    RISE_PANEL_V1,
    soft_promote_score,
)
from atlas.paper.rise_panel_scalp_dual_thrust_1h_eval import (
    SCALP_4H_ID,
    SCALP_EMA1221_1H_ID,
    SCALP_IMPROVE_ID,
    SCALP_PROVISIONAL_ID,
    deltas_vs_ref,
)
from atlas.strategy.dual_thrust import prior_hh_ll_range
from atlas.strategy.scalp_doge_dual_thrust_1h import (
    BAR,
    FAMILY,
    FLAT,
    K1,
    K2,
    LOOKBACK,
    LONG,
    SLEEVE,
    ScalpDogeDualThrust1hParams,
    ScalpDogeDualThrust1hV1,
)
from atlas.paper.types import Bar

BAR_MS = 60 * 60 * 1000
START = 1_600_000_000_000
SYM = "DOGE-USDT"


def _bar(i: int, o: float, h: float, l: float, c: float) -> Bar:
    ts = START + i * BAR_MS
    return Bar(SYM, ts, ts + BAR_MS, o, h, l, c, 1.0, True, "test")


def _ohlc_from_close(i: int, c: float, *, wide: float = 0.02) -> Bar:
    return _bar(i, c, c + wide, c - wide, c)


def test_ids_and_sleeve_locked():
    assert SCALP_PROVISIONAL_ID == "rise_panel_v1_scalp_doge_ema12_30_1h_daily_bull_eur20"
    assert SCALP_4H_ID == "rise_panel_v1_scalp_doge_ema12_30_4h_eur20"
    assert SCALP_EMA1221_1H_ID == "rise_panel_v1_scalp_doge_ema12_21_1h_eur20"
    assert SCALP_IMPROVE_ID == "rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_1h_eur20"
    assert SCALP_START_EUR == 20.0
    assert PANEL_LABEL == "rise_panel_v1"
    assert len(RISE_PANEL_V1) == 7


def test_family_dual_thrust_locked():
    assert FAMILY == "dual_thrust_n20_k0505_long_flat_1h"
    assert BAR == "1H"
    assert LOOKBACK == 20
    assert K1 == 0.5
    assert K2 == 0.5
    assert SLEEVE == "scalp"
    s = ScalpDogeDualThrust1hV1()
    assert "scalp_doge_dual_thrust_1h" in s.label
    assert s.warmup_bars() == LOOKBACK + 1


def test_rejects_param_tf_sleeve_sweeps():
    with pytest.raises(ValueError, match="param"):
        ScalpDogeDualThrust1hV1(ScalpDogeDualThrust1hParams(lookback=30))
    with pytest.raises(ValueError, match="param"):
        ScalpDogeDualThrust1hV1(ScalpDogeDualThrust1hParams(k1=0.6))
    with pytest.raises(ValueError, match="param"):
        ScalpDogeDualThrust1hV1(ScalpDogeDualThrust1hParams(k2=0.4))
    with pytest.raises(ValueError, match="bar"):
        ScalpDogeDualThrust1hV1(ScalpDogeDualThrust1hParams(bar="4H"))
    with pytest.raises(ValueError, match="sleeve"):
        ScalpDogeDualThrust1hV1(ScalpDogeDualThrust1hParams(sleeve="mid"))


def test_hh_ll_range_exclusive():
    bars = [_ohlc_from_close(i, 1.0 + 0.01 * i, wide=0.05) for i in range(25)]
    rng = prior_hh_ll_range(bars, 20)
    assert rng is not None
    # prior window = bars[-21:-1]
    window = bars[-21:-1]
    assert abs(rng - (max(b.high for b in window) - min(b.low for b in window))) < 1e-12


def test_breakout_up_goes_long_then_sell_breaks_flat():
    bars: list[Bar] = []
    for i in range(25):
        bars.append(_ohlc_from_close(i, 1.0, wide=0.01))
    bars.append(_bar(25, 1.0, 1.20, 0.99, 1.15))
    strat = ScalpDogeDualThrust1hV1()
    assert strat.desired_state(bars) == LONG
    for j in range(10):
        bars.append(_ohlc_from_close(26 + j, 1.15 - 0.01 * j, wide=0.01))
    bars.append(_bar(36, 1.05, 1.06, 0.80, 0.82))
    assert strat.desired_state(bars) == FLAT


def test_never_short():
    bars = [_ohlc_from_close(i, 1.0 + 0.01 * ((-1) ** i) * (i % 5), wide=0.05) for i in range(80)]
    strat = ScalpDogeDualThrust1hV1()
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
            "n_exp_gt_0": 5,
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
    assert d["n_exp_gt_0"]["delta"] == 1
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
