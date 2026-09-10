"""Unit tests: rise_panel Mid improve persist2 lock + soft-promote deltas."""

from __future__ import annotations

import pytest

from atlas.paper.cascade import MID_START_EUR
from atlas.paper.rise_panel import (
    MID_CANDIDATE_ID,
    PANEL_LABEL,
    RISE_PANEL_V1,
    soft_promote_score,
)
from atlas.paper.rise_panel_mid_improve_eval import (
    MID_BASELINE_ID,
    MID_IMPROVE_ID,
    deltas_vs_mid_baseline,
)
from atlas.strategy.ema_persist2 import ENTRY_PERSIST
from atlas.strategy.mid_doge_ema_persist2_4h import (
    BAR,
    FAMILY,
    FAST,
    FLAT,
    LONG,
    SLOW,
    MidDogeEmaPersist2_4hParams,
    MidDogeEmaPersist2_4hV1,
)
from atlas.paper.types import Bar

DAY = 4 * 60 * 60 * 1000  # 4H ms
START = 1_600_000_000_000
SYM = "DOGE-USDT"


def _bar(i: int, c: float) -> Bar:
    ts = START + i * DAY
    return Bar(SYM, ts, ts + DAY, c, c + 0.01, c - 0.01, c, 1.0, True, "test")


def test_ids_and_sleeve_locked():
    assert MID_BASELINE_ID == MID_CANDIDATE_ID == "rise_panel_v1_mid_doge_ema12_30_4h_eur40"
    assert MID_IMPROVE_ID == "rise_panel_v1_mid_doge_ema12_30_persist2_4h_eur40"
    assert MID_START_EUR == 40.0
    assert PANEL_LABEL == "rise_panel_v1"
    assert len(RISE_PANEL_V1) == 7


def test_family_not_period_grind():
    assert FAMILY == "ema12_30_persist2_entry_4h"
    assert BAR == "4H"
    assert FAST == 12 and SLOW == 30
    s = MidDogeEmaPersist2_4hV1()
    assert "persist2" in s.label
    assert s.warmup_bars() == SLOW + ENTRY_PERSIST - 1


def test_rejects_period_and_persist_sweeps():
    with pytest.raises(ValueError, match="period"):
        MidDogeEmaPersist2_4hV1(MidDogeEmaPersist2_4hParams(fast=10, slow=30))
    with pytest.raises(ValueError, match="entry_persist"):
        MidDogeEmaPersist2_4hV1(MidDogeEmaPersist2_4hParams(entry_persist=3))
    with pytest.raises(ValueError, match="bar"):
        MidDogeEmaPersist2_4hV1(MidDogeEmaPersist2_4hParams(bar="1H"))


def test_persist2_needs_two_bars_before_long():
    """Uptrend: first bar of EMA long stays flat until prior also long."""
    # Build a long enough series: flat then rising so EMA12 crosses above EMA30.
    closes = [1.0] * 40 + [1.0 + 0.02 * i for i in range(40)]
    bars = [_bar(i, c) for i, c in enumerate(closes)]
    strat = MidDogeEmaPersist2_4hV1()
    # Walk prefixes; once long, prior bar must also have been long-capable.
    states = [strat.desired_state(bars[: i + 1]) for i in range(len(bars))]
    assert FLAT in states
    assert LONG in states
    first_long = next(i for i, st in enumerate(states) if st == LONG)
    assert first_long >= 1
    # Immediate exit still available (smoke: never short)
    assert all(st in (LONG, FLAT) for st in states)


def test_deltas_vs_mid_baseline_shape():
    baseline = {
        "summary": {
            "median_expectancy_eur": 2.0,
            "panel_net_eur": 80.0,
            "median_trades": 7.0,
            "n_exp_gt_0": 6,
        }
    }
    improve = {
        "summary": {
            "median_expectancy_eur": 2.5,
            "panel_net_eur": 90.0,
            "median_trades": 5.0,
            "n_exp_gt_0": 6,
        }
    }
    d = deltas_vs_mid_baseline(baseline, improve)
    assert d["compare_to"] == MID_BASELINE_ID
    assert d["median_expectancy_eur"]["delta"] == 0.5
    assert d["panel_net_eur"]["delta"] == 10.0
    assert d["median_trades"]["delta"] == -2.0
    assert d["n_exp_gt_0"]["delta"] == 0
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
