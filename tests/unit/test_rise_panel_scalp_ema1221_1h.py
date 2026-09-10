"""Unit tests: rise_panel Scalp #63 EMA12/21 1H lock + soft-promote deltas."""

from __future__ import annotations

import pytest

from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.rise_panel import (
    PANEL_LABEL,
    RISE_PANEL_V1,
    soft_promote_score,
)
from atlas.paper.rise_panel_scalp_ema1221_1h_eval import (
    SCALP_4H_ID,
    SCALP_BREAKOUT_ID,
    SCALP_DONCHIAN_ID,
    SCALP_IMPROVE_ID,
    SCALP_PROVISIONAL_ID,
    SCALP_RSI_MR_ID,
    deltas_vs_ref,
)
from atlas.strategy.scalp_doge_ema1221_1h import (
    BAR,
    FAMILY,
    FAST,
    FLAT,
    LONG,
    SLEEVE,
    SLOW,
    ScalpDogeEma1221Params,
    ScalpDogeEma1221V1,
)
from atlas.paper.types import Bar

BAR_MS = 60 * 60 * 1000
START = 1_600_000_000_000
SYM = "DOGE-USDT"


def _bar(i: int, c: float) -> Bar:
    ts = START + i * BAR_MS
    return Bar(SYM, ts, ts + BAR_MS, c, c + 0.01, c - 0.01, c, 1.0, True, "test")


def test_ids_and_sleeve_locked():
    assert SCALP_PROVISIONAL_ID == "rise_panel_v1_scalp_doge_ema12_30_1h_daily_bull_eur20"
    assert SCALP_4H_ID == "rise_panel_v1_scalp_doge_ema12_30_4h_eur20"
    assert SCALP_DONCHIAN_ID == "rise_panel_v1_scalp_doge_donchian20_10_1h_eur20"
    assert SCALP_BREAKOUT_ID == "rise_panel_v1_scalp_doge_breakoutv1_1h_eur20"
    assert SCALP_RSI_MR_ID == "rise_panel_v1_scalp_doge_rsi14_mr_1h_eur20"
    assert SCALP_IMPROVE_ID == "rise_panel_v1_scalp_doge_ema12_21_1h_eur20"
    assert SCALP_START_EUR == 20.0
    assert PANEL_LABEL == "rise_panel_v1"
    assert len(RISE_PANEL_V1) == 7


def test_family_ema1221_locked():
    assert FAMILY == "ema12_21_long_flat_1h"
    assert BAR == "1H"
    assert FAST == 12
    assert SLOW == 21
    assert SLOW != 30
    assert SLEEVE == "scalp"
    s = ScalpDogeEma1221V1()
    assert "scalp_doge_ema1221_1h" in s.label
    assert s.warmup_bars() == SLOW


def test_rejects_period_tf_sleeve_sweeps():
    with pytest.raises(ValueError, match="period"):
        ScalpDogeEma1221V1(ScalpDogeEma1221Params(slow=30))
    with pytest.raises(ValueError, match="period"):
        ScalpDogeEma1221V1(ScalpDogeEma1221Params(fast=8))
    with pytest.raises(ValueError, match="bar"):
        ScalpDogeEma1221V1(ScalpDogeEma1221Params(bar="4H"))
    with pytest.raises(ValueError, match="sleeve"):
        ScalpDogeEma1221V1(ScalpDogeEma1221Params(sleeve="mid"))


def test_uptrend_long_downtrend_flat():
    # Rising closes → EMA12 > EMA21 after warmup → long
    closes_up = [1.0 + 0.01 * i for i in range(60)]
    bars_up = [_bar(i, c) for i, c in enumerate(closes_up)]
    strat = ScalpDogeEma1221V1()
    assert strat.desired_state(bars_up) == LONG
    # Falling closes after rise → eventually flat
    closes_dn = closes_up + [closes_up[-1] - 0.05 * (i + 1) for i in range(40)]
    bars_dn = [_bar(i, c) for i, c in enumerate(closes_dn)]
    assert strat.desired_state(bars_dn) == FLAT


def test_never_short():
    closes = [1.0 + 0.02 * ((-1) ** i) * i for i in range(80)]
    bars = [_bar(i, abs(c) + 0.5) for i, c in enumerate(closes)]
    strat = ScalpDogeEma1221V1()
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
