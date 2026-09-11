"""Unit tests: rise_panel Mid #68 MACD(12,26,9) 4H lock + soft-promote deltas."""

from __future__ import annotations

import pytest

from atlas.paper.cascade import CORE_START_EUR, MID_START_EUR
from atlas.paper.rise_panel import (
    MID_BASELINE_ID,
    MID_BREAKOUT_ARCHIVE_ID,
    MID_CANDIDATE_ID,
    MID_EMA_ARCHIVE_ID,
    PANEL_LABEL,
    RISE_PANEL_V1,
    soft_promote_score,
)
from atlas.paper.rise_panel_mid_macd_4h_eval import (
    CORE_MID_BOOK_EUR,
    CORE_MID_BOOK_ID,
    MID_BREAKOUT_BASELINE_ID,
    MID_IMPROVE_ID,
    deltas_vs_ema_archive,
    deltas_vs_mid_baseline,
)
from atlas.strategy.mid_doge_macd_4h import (
    BAR,
    FAMILY,
    FAST,
    FLAT,
    LONG,
    SIGNAL,
    SLEEVE,
    SLOW,
    MidDogeMacd4hParams,
    MidDogeMacd4hV1,
)
from atlas.paper.types import Bar

BAR_MS = 4 * 60 * 60 * 1000
START = 1_600_000_000_000
SYM = "DOGE-USDT"


def _bar(i: int, c: float) -> Bar:
    ts = START + i * BAR_MS
    return Bar(SYM, ts, ts + BAR_MS, c, c + 0.01, c - 0.01, c, 1.0, True, "test")


def test_ids_and_sleeve_locked():
    assert MID_BREAKOUT_BASELINE_ID == MID_BREAKOUT_ARCHIVE_ID
    assert MID_BREAKOUT_ARCHIVE_ID == "rise_panel_v1_mid_doge_breakoutv1_4h_eur40"
    assert MID_BASELINE_ID == "rise_panel_v1_mid_doge_breakoutv1_ema1221_long_4h_eur40"
    assert MID_EMA_ARCHIVE_ID == MID_CANDIDATE_ID
    assert MID_EMA_ARCHIVE_ID == "rise_panel_v1_mid_doge_ema12_30_4h_eur40"
    assert MID_IMPROVE_ID == "rise_panel_v1_mid_doge_macd12269_4h_eur40"
    assert MID_START_EUR == 40.0
    assert CORE_START_EUR == 140.0
    assert CORE_MID_BOOK_EUR == 180.0
    assert CORE_MID_BOOK_ID == "rise_panel_v1_core_mid_book_180_mid_macd12269_4h"
    assert PANEL_LABEL == "rise_panel_v1"
    assert len(RISE_PANEL_V1) == 7


def test_family_macd_locked():
    assert FAMILY == "macd12269_long_flat_4h"
    assert BAR == "4H"
    assert FAST == 12
    assert SLOW == 26
    assert SIGNAL == 9
    assert SLEEVE == "mid"
    s = MidDogeMacd4hV1()
    assert "mid_doge_macd_4h" in s.label
    assert s.warmup_bars() >= SLOW + SIGNAL - 1


def test_rejects_period_tf_sleeve_sweeps():
    with pytest.raises(ValueError, match="period"):
        MidDogeMacd4hV1(MidDogeMacd4hParams(fast=12, slow=26, signal=12))
    with pytest.raises(ValueError, match="period"):
        MidDogeMacd4hV1(MidDogeMacd4hParams(fast=8, slow=26, signal=9))
    with pytest.raises(ValueError, match="bar"):
        MidDogeMacd4hV1(MidDogeMacd4hParams(bar="1H"))
    with pytest.raises(ValueError, match="sleeve"):
        MidDogeMacd4hV1(MidDogeMacd4hParams(sleeve="scalp"))


def test_long_flat_on_trend_and_never_short():
    # down then up so MACD×signal cross happens
    closes: list[float] = [100.0 - i * 0.5 for i in range(50)]
    closes += [closes[-1] + i * 0.8 for i in range(1, 60)]
    bars = [_bar(i, c) for i, c in enumerate(closes)]
    strat = MidDogeMacd4hV1()
    states = [strat.desired_state(bars[: i + 1]) for i in range(len(bars))]
    assert FLAT in states
    assert LONG in states
    assert all(st in (LONG, FLAT) for st in states)
    assert not hasattr(strat, "set_daily_bars")
    assert not hasattr(strat, "rsi_filter")


def test_deltas_vs_breakout_baseline_shape():
    baseline = {
        "summary": {
            "median_expectancy_eur": 2.4647,
            "panel_net_eur": 95.4483,
            "median_trades": 6.0,
            "n_exp_gt_0": 5,
        }
    }
    improve = {
        "summary": {
            "median_expectancy_eur": 1.0,
            "panel_net_eur": 50.0,
            "median_trades": 8.0,
            "n_exp_gt_0": 6,
        }
    }
    d = deltas_vs_mid_baseline(baseline, improve)
    assert d["compare_to"] == MID_BREAKOUT_BASELINE_ID
    assert d["improve_id"] == MID_IMPROVE_ID
    assert abs(d["panel_net_eur"]["delta"] - (50.0 - 95.4483)) < 1e-6
    assert d["promote_as_better"] is False
    assert d["n_exp_gt_0"]["delta"] == 1

    better = {
        "summary": {
            "median_expectancy_eur": 3.0,
            "panel_net_eur": 100.0,
            "median_trades": 6.0,
            "n_exp_gt_0": 5,
        }
    }
    d2 = deltas_vs_mid_baseline(baseline, better)
    assert d2["promote_as_better"] is True


def test_deltas_vs_ema_archive_shape():
    improve = {
        "summary": {
            "median_expectancy_eur": 1.0,
            "panel_net_eur": 50.0,
            "median_trades": 8.0,
            "n_exp_gt_0": 5,
        }
    }
    d = deltas_vs_ema_archive(improve)
    assert d["compare_to"] == MID_EMA_ARCHIVE_ID
    assert abs(d["panel_net_eur"]["delta"] - (50.0 - 83.6104)) < 1e-6


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
