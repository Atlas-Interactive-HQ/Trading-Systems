"""Unit tests: rise_panel Scalp improve 15m EMA lock + soft-promote deltas (#58)."""

from __future__ import annotations

import pytest

from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.rise_panel import (
    PANEL_LABEL,
    RISE_PANEL_V1,
    soft_promote_score,
)
from atlas.paper.rise_panel_scalp_improve_15m_eval import (
    SCALP_4H_ID,
    SCALP_IMPROVE_ID,
    SCALP_PROVISIONAL_ID,
    deltas_vs_ref,
)
from atlas.strategy.scalp_doge_ema_15m import (
    BAR,
    FAMILY,
    FAST,
    FLAT,
    LONG,
    SLEEVE,
    SLOW,
    ScalpDogeEma15mParams,
    ScalpDogeEma15mV1,
)
from atlas.paper.types import Bar

BAR_MS = 15 * 60 * 1000
START = 1_600_000_000_000
SYM = "DOGE-USDT"


def _bar(i: int, c: float) -> Bar:
    ts = START + i * BAR_MS
    return Bar(SYM, ts, ts + BAR_MS, c, c + 0.01, c - 0.01, c, 1.0, True, "test")


def test_ids_and_sleeve_locked():
    assert SCALP_PROVISIONAL_ID == "rise_panel_v1_scalp_doge_ema12_30_1h_daily_bull_eur20"
    assert SCALP_4H_ID == "rise_panel_v1_scalp_doge_ema12_30_4h_eur20"
    assert SCALP_IMPROVE_ID == "rise_panel_v1_scalp_doge_ema12_30_15m_eur20"
    assert SCALP_START_EUR == 20.0
    assert PANEL_LABEL == "rise_panel_v1"
    assert len(RISE_PANEL_V1) == 7


def test_family_matches_mid_baseline_not_period_grind():
    assert FAMILY == "ema12_30_long_flat_15m"
    assert BAR == "15m"
    assert FAST == 12 and SLOW == 30
    assert SLEEVE == "scalp"
    s = ScalpDogeEma15mV1()
    assert "scalp_doge_ema_15m" in s.label
    assert s.warmup_bars() == SLOW


def test_rejects_period_tf_sleeve_sweeps():
    with pytest.raises(ValueError, match="period"):
        ScalpDogeEma15mV1(ScalpDogeEma15mParams(fast=10, slow=30))
    with pytest.raises(ValueError, match="bar"):
        ScalpDogeEma15mV1(ScalpDogeEma15mParams(bar="1H"))
    with pytest.raises(ValueError, match="sleeve"):
        ScalpDogeEma15mV1(ScalpDogeEma15mParams(sleeve="mid"))


def test_long_flat_never_short():
    closes = [1.0] * 40 + [1.0 + 0.02 * i for i in range(40)]
    bars = [_bar(i, c) for i, c in enumerate(closes)]
    strat = ScalpDogeEma15mV1()
    states = [strat.desired_state(bars[: i + 1]) for i in range(len(bars))]
    assert FLAT in states
    assert LONG in states
    assert all(st in (LONG, FLAT) for st in states)


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
            "median_trades": 40.0,
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
    assert d["median_trades"]["delta"] == 22.0
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
    assert sc["verdict"] == "PASS"


def test_cascade_modes_include_15m():
    from atlas.paper.rise_panel_cascade_eval import SCALP_MODES, SCALP_CANDIDATE_ID_15M

    assert "15m_ema" in SCALP_MODES
    assert SCALP_CANDIDATE_ID_15M == SCALP_IMPROVE_ID
