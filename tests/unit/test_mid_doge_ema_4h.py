"""Unit tests: Mid DOGE EMA12/30 4H Core-style RETURN gate (#45)."""

from __future__ import annotations

from atlas.paper.cascade import MID_START_EUR
from atlas.paper.mid_doge_ema_4h_eval import (
    BAR,
    BH_DD_MULT,
    DIFFERS_FROM_HOLDOUT_EXP_GATE,
    DIFFERS_REASON,
    FAMILY,
    FAST,
    GATE_NAME,
    MID_DD_ABS_CAP_EUR,
    PRIOR_HOLDOUT_EXP_TRIALS,
    SLOW,
    SOURCE,
    SPOT_MD,
    TIM_HIGH,
    aggregate_set,
    score_mid,
)
from atlas.strategy.ema_trend import FLAT
from atlas.strategy.mid_doge_ema_4h import MidDogeEma4hParams, MidDogeEma4hV1


def test_locked_params():
    assert SPOT_MD == "DOGE-USDT"
    assert BAR == "4H"
    assert FAST == 12 and SLOW == 30
    assert MID_START_EUR == 40.0
    assert MID_DD_ABS_CAP_EUR == 20.0
    assert BH_DD_MULT == 1.10
    assert TIM_HIGH == 0.80
    assert FAMILY == "ema12_30_long_flat_4h"
    assert GATE_NAME == "core_style_return"
    assert SOURCE == "mid_doge_ema_4h"
    assert DIFFERS_FROM_HOLDOUT_EXP_GATE is True
    assert "thin/zero holdout n" in DIFFERS_REASON
    assert "#36" in PRIOR_HOLDOUT_EXP_TRIALS and "#44" in PRIOR_HOLDOUT_EXP_TRIALS
    assert "#41" not in PRIOR_HOLDOUT_EXP_TRIALS  # #41 already core_style_return


def test_strategy_never_short_and_label():
    strat = MidDogeEma4hV1(MidDogeEma4hParams(fast=12, slow=30))
    assert strat.label.startswith("mid_doge_ema_4h")
    assert strat.desired_state([]) == FLAT
    assert strat.warmup_bars() == 30


def test_score_mid_return_pass_with_bh_dd():
    full = {
        "ok": True,
        "n_trades": 0,
        "net_return_eur": 8.0,
        "max_dd_eur": 5.0,
        "bh_max_dd_eur": 5.0,
        "time_in_market": 1.0,
        "expectancy_after_costs_eur": None,
    }
    hold = {
        "ok": True,
        "n_trades": 0,
        "net_return_eur": 1.2,
        "max_dd_eur": 1.0,
        "bh_max_dd_eur": 1.0,
        "time_in_market": 1.0,
        "expectancy_after_costs_eur": None,
    }
    sc = score_mid(full, hold)
    assert sc["gate_mode"] == "core_style_return"
    assert sc["differs_from_holdout_exp_gate"] is True
    assert sc["full_pass"] is True
    assert sc["holdout_ok_if_full_passed"] is True
    assert sc["full_dd_within_cap"] is True


def test_score_mid_dd_vs_bh_fail():
    full = {
        "ok": True,
        "n_trades": 1,
        "net_return_eur": 3.0,
        "max_dd_eur": 12.0,
        "bh_max_dd_eur": 10.0,  # 12 > 11 → fail
        "time_in_market": 0.5,
        "expectancy_after_costs_eur": 3.0,
    }
    sc = score_mid(full, None)
    assert sc["full_pass"] is False
    assert sc["full_dd_within_cap"] is False


def test_score_mid_abs_dd_when_no_bh():
    full = {
        "ok": True,
        "n_trades": 2,
        "net_return_eur": 4.0,
        "max_dd_eur": 18.0,
        "bh_max_dd_eur": None,
        "time_in_market": 0.4,
        "expectancy_after_costs_eur": 2.0,
    }
    hold = {
        "ok": True,
        "n_trades": 1,
        "net_return_eur": 0.5,
        "max_dd_eur": 1.0,
        "bh_max_dd_eur": None,
        "time_in_market": 0.3,
        "expectancy_after_costs_eur": 0.5,
    }
    sc = score_mid(full, hold)
    assert sc["full_pass"] is True  # 18 <= 20
    assert sc["holdout_ok_if_full_passed"] is True


def test_score_mid_holdout_zero_trade_low_tim_fail():
    full = {
        "ok": True,
        "n_trades": 0,
        "net_return_eur": 5.0,
        "max_dd_eur": 4.0,
        "bh_max_dd_eur": 4.0,
        "time_in_market": 1.0,
        "expectancy_after_costs_eur": None,
    }
    hold = {
        "ok": True,
        "n_trades": 0,
        "net_return_eur": 1.0,
        "max_dd_eur": 0.5,
        "bh_max_dd_eur": 0.5,
        "time_in_market": 0.1,
        "expectancy_after_costs_eur": None,
    }
    sc = score_mid(full, hold)
    assert sc["full_pass"] is True
    assert sc["holdout_ok_if_full_passed"] is False


def test_score_mid_holdout_net_negative_fail():
    full = {
        "ok": True,
        "n_trades": 1,
        "net_return_eur": 5.0,
        "max_dd_eur": 3.0,
        "bh_max_dd_eur": 4.0,
        "time_in_market": 0.6,
        "expectancy_after_costs_eur": 5.0,
    }
    hold = {
        "ok": True,
        "n_trades": 1,
        "net_return_eur": -0.5,
        "max_dd_eur": 1.0,
        "bh_max_dd_eur": 1.0,
        "time_in_market": 0.4,
        "expectancy_after_costs_eur": -0.5,
    }
    sc = score_mid(full, hold)
    assert sc["full_pass"] is True
    assert sc["holdout_ok_if_full_passed"] is False


def test_aggregate_requires_two_clean():
    def _wr(wid: str, *, full_pass: bool, hold_ok: bool | None, n: int, tim: float = 1.0) -> dict:
        return {
            "window_id": wid,
            "mid": {
                "full": {"n_trades": n, "ok": True, "time_in_market": tim},
                "score": {
                    "missing_or_nan": False,
                    "full_pass": full_pass,
                    "full_net_return_gt_0": full_pass,
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
    assert ok["mid"]["differs_from_holdout_exp_gate"] is True

    fail_one_clean = aggregate_set(
        [
            _wr("A1", full_pass=True, hold_ok=True, n=0),
            _wr("A2", full_pass=True, hold_ok=False, n=0),
            _wr("A3", full_pass=False, hold_ok=None, n=1),
        ]
    )
    assert fail_one_clean["verdict"] == "FAIL"
    assert fail_one_clean["mid"]["clean_pass_windows"] == ["A1"]

    pass_with_extra_red = aggregate_set(
        [
            _wr("A1", full_pass=True, hold_ok=True, n=0),
            _wr("A2", full_pass=True, hold_ok=True, n=0),
            _wr("A3", full_pass=True, hold_ok=False, n=1),
        ]
    )
    assert pass_with_extra_red["verdict"] == "PASS"
    assert pass_with_extra_red["mid"]["clean_pass_windows"] == ["A1", "A2"]


def test_not_using_expectancy_gate():
    """Positive expectancy alone must NOT pass if net return ≤ 0."""
    full = {
        "ok": True,
        "n_trades": 3,
        "net_return_eur": -1.0,
        "max_dd_eur": 2.0,
        "bh_max_dd_eur": 5.0,
        "time_in_market": 0.5,
        "expectancy_after_costs_eur": 0.5,
    }
    sc = score_mid(full, None)
    assert sc["gate_mode"] == "core_style_return"
    assert sc["full_pass"] is False
    assert sc["full_net_return_gt_0"] is False
