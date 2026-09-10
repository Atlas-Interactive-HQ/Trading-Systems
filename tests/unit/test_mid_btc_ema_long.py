"""Unit tests: Mid BTC EMA12/30 long-only — Core family at Mid sleeve."""

from __future__ import annotations

from atlas.paper.mid_btc_ema_long_eval import (
    FAMILY,
    FAST,
    LOW_FREQ_MEDIAN_CAP,
    MID_DD_CAP_EUR,
    SLOW,
    SOURCE,
    SPOT_MD,
    aggregate_set,
    score_mid,
)
from atlas.paper.cascade import MID_START_EUR
from atlas.strategy.ema_trend import FLAT, LONG, EmaTrendParams, EmaTrendV1


def test_locked_params():
    assert SPOT_MD == "BTC-USDT"
    assert FAST == 12 and SLOW == 30
    assert MID_DD_CAP_EUR == 16.0
    assert MID_START_EUR == 40.0
    assert LOW_FREQ_MEDIAN_CAP == 15
    assert FAMILY == "ema12_30_long_flat"
    assert SOURCE == "mid_btc_ema_long"


def test_ema_trend_never_short():
    strat = EmaTrendV1(EmaTrendParams(fast=12, slow=30))
    assert strat.label.startswith("ema_long_flat")
    # empty → flat
    assert strat.desired_state([]) == FLAT


def test_score_mid_zero_trade_core_style_pass():
    full = {
        "ok": True,
        "n_trades": 0,
        "net_return_eur": 5.0,
        "max_dd_eur": 4.0,
        "expectancy_after_costs_eur": None,
    }
    hold = {
        "ok": True,
        "n_trades": 0,
        "net_return_eur": 1.5,
        "max_dd_eur": 2.0,
        "bh_max_dd_eur": 2.0,
        "expectancy_after_costs_eur": None,
    }
    sc = score_mid(full, hold, dd_cap_eur=16.0)
    assert sc["gate_mode"] == "zero_trade_core_style_return"
    assert sc["full_pass"] is True
    assert sc["holdout_ok_if_full_passed"] is True


def test_score_mid_zero_trade_dd_fail():
    full = {
        "ok": True,
        "n_trades": 0,
        "net_return_eur": 10.0,
        "max_dd_eur": 19.0,
        "expectancy_after_costs_eur": None,
    }
    sc = score_mid(full, None, dd_cap_eur=16.0)
    assert sc["full_pass"] is False
    assert sc["full_dd_within_cap"] is False


def test_score_mid_zero_trade_holdout_bh_incompatible():
    full = {
        "ok": True,
        "n_trades": 0,
        "net_return_eur": 5.0,
        "max_dd_eur": 4.0,
        "expectancy_after_costs_eur": None,
    }
    hold = {
        "ok": True,
        "n_trades": 0,
        "net_return_eur": 1.0,
        "max_dd_eur": 3.0,
        "bh_max_dd_eur": 2.0,  # DD > BH → fail
        "expectancy_after_costs_eur": None,
    }
    sc = score_mid(full, hold, dd_cap_eur=16.0)
    assert sc["full_pass"] is True
    assert sc["holdout_ok_if_full_passed"] is False


def test_score_mid_expectancy_gate():
    full = {
        "ok": True,
        "n_trades": 2,
        "net_return_eur": 3.0,
        "max_dd_eur": 5.0,
        "expectancy_after_costs_eur": 1.2,
    }
    hold = {
        "ok": True,
        "n_trades": 1,
        "net_return_eur": 0.5,
        "max_dd_eur": 1.0,
        "bh_max_dd_eur": 1.0,
        "expectancy_after_costs_eur": 0.4,
    }
    sc = score_mid(full, hold, dd_cap_eur=16.0)
    assert sc["gate_mode"] == "n_trades_expectancy"
    assert sc["full_pass"] is True
    assert sc["holdout_ok_if_full_passed"] is True


def test_aggregate_requires_two_full_and_holdouts():
    def _wr(wid: str, *, full_pass: bool, hold_ok: bool | None, n: int) -> dict:
        return {
            "window_id": wid,
            "mid": {
                "full": {"n_trades": n, "ok": True},
                "score": {
                    "missing_or_nan": False,
                    "full_pass": full_pass,
                    "full_expectancy_gt_0": full_pass and n >= 1,
                    "full_net_return_gt_0": full_pass and n == 0,
                    "full_dd_within_cap": True,
                    "holdout_ok_if_full_passed": hold_ok,
                },
            },
        }

    ok = aggregate_set(
        [
            _wr("A1", full_pass=True, hold_ok=True, n=0),
            _wr("A2", full_pass=False, hold_ok=None, n=0),
            _wr("A3", full_pass=True, hold_ok=True, n=1),
        ]
    )
    assert ok["verdict"] == "PASS"
    assert ok["mid"]["pass"] is True

    fail_hold = aggregate_set(
        [
            _wr("A1", full_pass=True, hold_ok=True, n=0),
            _wr("A2", full_pass=True, hold_ok=False, n=0),
            _wr("A3", full_pass=False, hold_ok=None, n=1),
        ]
    )
    assert fail_hold["verdict"] == "FAIL"
    assert "A2" in fail_hold["mid"]["holdout_fail_windows"]
