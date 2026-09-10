"""Unit tests: rise_panel Mid #64 Donchian 20/10 4H lock + soft-promote deltas."""

from __future__ import annotations

import pytest

from atlas.paper.cascade import CORE_START_EUR, MID_START_EUR
from atlas.paper.rise_panel import (
    MID_CANDIDATE_ID,
    PANEL_LABEL,
    RISE_PANEL_V1,
    soft_promote_score,
)
from atlas.paper.rise_panel_mid_donchian_4h_eval import (
    CORE_MID_BOOK_EUR,
    CORE_MID_BOOK_ID,
    MID_BASELINE_ID,
    MID_IMPROVE_ID,
    deltas_vs_mid_baseline,
)
from atlas.strategy.mid_doge_donchian_4h import (
    BAR,
    ENTRY_LOOKBACK,
    EXIT_LOOKBACK,
    FAMILY,
    FLAT,
    LONG,
    SLEEVE,
    MidDogeDonchian4hParams,
    MidDogeDonchian4hV1,
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


def test_ids_and_sleeve_locked():
    assert MID_BASELINE_ID == MID_CANDIDATE_ID
    assert MID_BASELINE_ID == "rise_panel_v1_mid_doge_ema12_30_4h_eur40"
    assert MID_IMPROVE_ID == "rise_panel_v1_mid_doge_donchian20_10_4h_eur40"
    assert MID_START_EUR == 40.0
    assert CORE_START_EUR == 140.0
    assert CORE_MID_BOOK_EUR == 180.0
    assert CORE_MID_BOOK_ID == "rise_panel_v1_core_mid_book_180_mid_donchian20_10_4h"
    assert PANEL_LABEL == "rise_panel_v1"
    assert len(RISE_PANEL_V1) == 7


def test_family_donchian_locked():
    assert FAMILY == "donchian20_10_long_flat_4h"
    assert BAR == "4H"
    assert ENTRY_LOOKBACK == 20
    assert EXIT_LOOKBACK == 10
    assert SLEEVE == "mid"
    s = MidDogeDonchian4hV1()
    assert "mid_doge_donchian_4h" in s.label
    assert s.warmup_bars() == max(ENTRY_LOOKBACK, EXIT_LOOKBACK) + 1


def test_rejects_lookback_tf_sleeve_sweeps():
    with pytest.raises(ValueError, match="lookback"):
        MidDogeDonchian4hV1(MidDogeDonchian4hParams(entry_lookback=16))
    with pytest.raises(ValueError, match="lookback"):
        MidDogeDonchian4hV1(MidDogeDonchian4hParams(exit_lookback=5))
    with pytest.raises(ValueError, match="bar"):
        MidDogeDonchian4hV1(MidDogeDonchian4hParams(bar="1H"))
    with pytest.raises(ValueError, match="sleeve"):
        MidDogeDonchian4hV1(MidDogeDonchian4hParams(sleeve="scalp"))


def test_entry_break_above_20_exit_below_10():
    """Canonical Donchian: break prior 20-high → long; break prior 10-low → flat."""
    bars = [_bar(i, 100.0, h=100.5, lo=99.5) for i in range(20)]
    bars.append(_bar(20, 101.0, h=101.5, lo=100.0))  # close > prior 100.5
    strat = MidDogeDonchian4hV1()
    assert strat.desired_state(bars) == LONG
    bars.append(_bar(21, 50.0, h=101.0, lo=49.0))
    assert strat.desired_state(bars) == FLAT


def test_never_short():
    closes = [1.0 + 0.01 * i for i in range(80)]
    bars = [_bar(i, c) for i, c in enumerate(closes)]
    strat = MidDogeDonchian4hV1()
    for i in range(len(bars)):
        assert strat.desired_state(bars[: i + 1]) in (LONG, FLAT)


def test_deltas_vs_mid_baseline_shape():
    baseline = {
        "summary": {
            "median_expectancy_eur": 2.0928,
            "panel_net_eur": 83.6104,
            "median_trades": 7.0,
            "n_exp_gt_0": 6,
        }
    }
    improve = {
        "summary": {
            "median_expectancy_eur": 1.0,
            "panel_net_eur": 50.0,
            "median_trades": 9.0,
            "n_exp_gt_0": 5,
        }
    }
    d = deltas_vs_mid_baseline(baseline, improve)
    assert d["compare_to"] == MID_BASELINE_ID
    assert d["improve_id"] == MID_IMPROVE_ID
    assert abs(d["panel_net_eur"]["delta"] - (50.0 - 83.6104)) < 1e-6
    assert d["n_exp_gt_0"]["delta"] == -1


def test_soft_promote_helper_still_works():
    rows = [
        {"ok": True, "n_trades": 5, "expectancy_after_costs_eur": 1.0, "net_return_eur": 5.0},
        {"ok": True, "n_trades": 4, "expectancy_after_costs_eur": 0.5, "net_return_eur": 2.0},
        {"ok": True, "n_trades": 6, "expectancy_after_costs_eur": 0.2, "net_return_eur": 1.0},
        {"ok": True, "n_trades": 3, "expectancy_after_costs_eur": 0.1, "net_return_eur": 0.5},
        {"ok": True, "n_trades": 7, "expectancy_after_costs_eur": 0.3, "net_return_eur": 2.0},
        {"ok": True, "n_trades": 2, "expectancy_after_costs_eur": -0.1, "net_return_eur": -0.2},
        {"ok": True, "n_trades": 8, "expectancy_after_costs_eur": 0.4, "net_return_eur": 3.0},
    ]
    soft = soft_promote_score(rows)
    assert soft["verdict"] == "PASS"
    assert soft["n_expectancy_gt_0"] == 6
