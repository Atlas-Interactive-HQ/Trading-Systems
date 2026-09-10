"""Unit tests: Scalp BTC EMA12/30 1D Core-style RETURN gate (#53)."""

from __future__ import annotations

from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.scalp_btc_ema_1d_eval import (
    BAR,
    BH_DD_MULT,
    CALENDARS_SAME_AS,
    DIFFERS_FROM_HOLDOUT_EXP_GATE,
    DIFFERS_REASON,
    FAMILY,
    FAST,
    GATE_NAME,
    PRIOR_HOLDOUT_EXP_TRIALS,
    SCALP_DD_ABS_CAP_EUR,
    SLOW,
    SOURCE,
    SPOT_MD,
    TIM_HIGH,
    aggregate_set,
    score_scalp,
)
from atlas.paper.three_tier_eval import ALT_SET_B, PRIMARY_SET_A
from atlas.strategy.ema_trend import FLAT
from atlas.strategy.scalp_btc_ema_1d import ScalpBtcEma1dParams, ScalpBtcEma1dV1


def test_locked_params():
    assert SPOT_MD == "BTC-USDT"
    assert BAR == "1D"
    assert FAST == 12 and SLOW == 30
    assert SCALP_START_EUR == 20.0
    assert SCALP_DD_ABS_CAP_EUR == 10.0
    assert BH_DD_MULT == 1.10
    assert TIM_HIGH == 0.80
    assert FAMILY == "ema12_30_long_flat_1d"
    assert GATE_NAME == "core_style_return"
    assert SOURCE == "scalp_btc_ema_1d"
    assert DIFFERS_FROM_HOLDOUT_EXP_GATE is True
    assert "thin/zero holdout n" in DIFFERS_REASON
    assert "Mid #51" in DIFFERS_REASON or "n≈0" in DIFFERS_REASON
    assert "#36" in PRIOR_HOLDOUT_EXP_TRIALS and "#44" in PRIOR_HOLDOUT_EXP_TRIALS
    assert "#41" not in PRIOR_HOLDOUT_EXP_TRIALS
    assert "#45" not in PRIOR_HOLDOUT_EXP_TRIALS
    assert "#49" not in PRIOR_HOLDOUT_EXP_TRIALS
    assert "#51" not in PRIOR_HOLDOUT_EXP_TRIALS
    assert "Mid #51" in CALENDARS_SAME_AS


def test_calendars_match_mid_51():
    """Same A/B calendars as Mid #51 (PRIMARY_SET_A / ALT_SET_B)."""
    assert [w.id for w in PRIMARY_SET_A] == ["A1", "A2", "A3"]
    assert PRIMARY_SET_A[0].start == "2023-10-01" and PRIMARY_SET_A[0].end == "2023-12-31"
    assert PRIMARY_SET_A[1].start == "2021-01-01" and PRIMARY_SET_A[1].end == "2021-03-31"
    assert PRIMARY_SET_A[2].start == "2024-02-01" and PRIMARY_SET_A[2].end == "2024-04-30"
    assert [w.id for w in ALT_SET_B] == ["B1", "B2", "B3"]
    assert ALT_SET_B[0].start == "2020-10-01" and ALT_SET_B[0].end == "2020-12-31"
    assert ALT_SET_B[1].start == "2023-01-01" and ALT_SET_B[1].end == "2023-03-31"
    assert ALT_SET_B[2].start == "2024-10-01" and ALT_SET_B[2].end == "2024-12-31"


def test_strategy_never_short_and_label():
    strat = ScalpBtcEma1dV1(ScalpBtcEma1dParams(fast=12, slow=30))
    assert strat.label.startswith("scalp_btc_ema_1d")
    assert strat.desired_state([]) == FLAT
    assert strat.warmup_bars() == 30
    assert strat.params.bar == "1D"
    assert strat.params.sleeve == "scalp"


def test_score_scalp_return_pass_with_bh_dd():
    full = {
        "ok": True,
        "n_trades": 0,
        "net_return_eur": 4.0,
        "max_dd_eur": 2.5,
        "bh_max_dd_eur": 2.5,
        "time_in_market": 1.0,
        "expectancy_after_costs_eur": None,
    }
    hold = {
        "ok": True,
        "n_trades": 0,
        "net_return_eur": 0.6,
        "max_dd_eur": 0.5,
        "bh_max_dd_eur": 0.5,
        "time_in_market": 1.0,
        "expectancy_after_costs_eur": None,
    }
    sc = score_scalp(full, hold)
    assert sc["gate_mode"] == "core_style_return"
    assert sc["differs_from_holdout_exp_gate"] is True
    assert sc["full_pass"] is True
    assert sc["holdout_ok_if_full_passed"] is True
    assert sc["full_dd_within_cap"] is True


def test_score_scalp_dd_vs_bh_fail():
    full = {
        "ok": True,
        "n_trades": 1,
        "net_return_eur": 1.5,
        "max_dd_eur": 6.0,
        "bh_max_dd_eur": 5.0,  # 6 > 5.5 → fail
        "time_in_market": 0.5,
        "expectancy_after_costs_eur": 1.5,
    }
    sc = score_scalp(full, None)
    assert sc["full_pass"] is False
    assert sc["full_dd_within_cap"] is False


def test_score_scalp_abs_dd_when_no_bh():
    full = {
        "ok": True,
        "n_trades": 2,
        "net_return_eur": 2.0,
        "max_dd_eur": 9.0,
        "bh_max_dd_eur": None,
        "time_in_market": 0.4,
        "expectancy_after_costs_eur": 1.0,
    }
    hold = {
        "ok": True,
        "n_trades": 1,
        "net_return_eur": 0.25,
        "max_dd_eur": 0.5,
        "bh_max_dd_eur": None,
        "time_in_market": 0.3,
        "expectancy_after_costs_eur": 0.25,
    }
    sc = score_scalp(full, hold)
    assert sc["full_pass"] is True  # 9 <= 10
    assert sc["holdout_ok_if_full_passed"] is True


def test_score_scalp_abs_dd_over_cap_fail():
    full = {
        "ok": True,
        "n_trades": 1,
        "net_return_eur": 1.0,
        "max_dd_eur": 10.5,
        "bh_max_dd_eur": None,
        "time_in_market": 0.4,
        "expectancy_after_costs_eur": 1.0,
    }
    sc = score_scalp(full, None)
    assert sc["full_pass"] is False
    assert sc["full_dd_within_cap"] is False


def test_score_scalp_holdout_zero_trade_low_tim_fail():
    full = {
        "ok": True,
        "n_trades": 0,
        "net_return_eur": 2.5,
        "max_dd_eur": 2.0,
        "bh_max_dd_eur": 2.0,
        "time_in_market": 1.0,
        "expectancy_after_costs_eur": None,
    }
    hold = {
        "ok": True,
        "n_trades": 0,
        "net_return_eur": 0.5,
        "max_dd_eur": 0.25,
        "bh_max_dd_eur": 0.25,
        "time_in_market": 0.1,
        "expectancy_after_costs_eur": None,
    }
    sc = score_scalp(full, hold)
    assert sc["full_pass"] is True
    assert sc["holdout_ok_if_full_passed"] is False


def test_score_scalp_holdout_net_negative_fail():
    full = {
        "ok": True,
        "n_trades": 1,
        "net_return_eur": 2.5,
        "max_dd_eur": 1.5,
        "bh_max_dd_eur": 2.0,
        "time_in_market": 0.6,
        "expectancy_after_costs_eur": 2.5,
    }
    hold = {
        "ok": True,
        "n_trades": 1,
        "net_return_eur": -0.25,
        "max_dd_eur": 0.5,
        "bh_max_dd_eur": 0.5,
        "time_in_market": 0.4,
        "expectancy_after_costs_eur": -0.25,
    }
    sc = score_scalp(full, hold)
    assert sc["full_pass"] is True
    assert sc["holdout_ok_if_full_passed"] is False


def test_aggregate_requires_two_clean():
    def _wr(wid: str, *, full_pass: bool, hold_ok: bool | None, n: int, tim: float = 1.0) -> dict:
        return {
            "window_id": wid,
            "scalp": {
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
    assert ok["scalp"]["pass"] is True
    assert ok["scalp"]["differs_from_holdout_exp_gate"] is True

    fail_one_clean = aggregate_set(
        [
            _wr("A1", full_pass=True, hold_ok=True, n=0),
            _wr("A2", full_pass=True, hold_ok=False, n=0),
            _wr("A3", full_pass=False, hold_ok=None, n=1),
        ]
    )
    assert fail_one_clean["verdict"] == "FAIL"
    assert fail_one_clean["scalp"]["clean_pass_windows"] == ["A1"]

    pass_with_extra_red = aggregate_set(
        [
            _wr("A1", full_pass=True, hold_ok=True, n=0),
            _wr("A2", full_pass=True, hold_ok=True, n=0),
            _wr("A3", full_pass=True, hold_ok=False, n=1),
        ]
    )
    assert pass_with_extra_red["verdict"] == "PASS"
    assert pass_with_extra_red["scalp"]["clean_pass_windows"] == ["A1", "A2"]


def test_not_using_expectancy_gate():
    """Positive expectancy alone must NOT pass if net return ≤ 0."""
    full = {
        "ok": True,
        "n_trades": 3,
        "net_return_eur": -0.5,
        "max_dd_eur": 1.0,
        "bh_max_dd_eur": 2.5,
        "time_in_market": 0.5,
        "expectancy_after_costs_eur": 0.25,
    }
    sc = score_scalp(full, None)
    assert sc["gate_mode"] == "core_style_return"
    assert sc["full_pass"] is False
    assert sc["full_net_return_gt_0"] is False


def test_is_mid51_scalp_twin_not_1h():
    """#53 is 1D Scalp twin of Mid #51 — not the 1H #50 trial."""
    assert BAR == "1D"
    assert SOURCE == "scalp_btc_ema_1d"
    assert FAMILY.endswith("_1d")
    assert SCALP_DD_ABS_CAP_EUR == 10.0
