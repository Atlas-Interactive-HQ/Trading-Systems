"""Unit tests: Scalp BTC EMA12/30 1H + daily bull Core-style RETURN gate (#50)."""

from __future__ import annotations

from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.scalp_btc_ema_1h_eval import (
    BAR,
    BH_DD_MULT,
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
    walk_long_flat_1h_daily_bull,
)
from atlas.paper.ema_eval import EmaBookSettings
from atlas.paper.types import Bar
from atlas.strategy.ema_trend import FLAT, LONG
from atlas.strategy.scalp_btc_ema_1h import ScalpBtcEma1hParams, ScalpBtcEma1hV1

BAR_MS = 60 * 60 * 1000
DAY_MS = 24 * 60 * 60 * 1000
START = 1_700_000_000_000


def b1h(i: int, c: float, symbol="BTC-USDT") -> Bar:
    ts = START + i * BAR_MS
    return Bar(symbol, ts, ts + BAR_MS, c, c + 0.01, c - 0.01, c, 10.0, True, "test")


def bday(i: int, c: float, symbol="BTC-USDT") -> Bar:
    ts = START + i * DAY_MS
    return Bar(symbol, ts, ts + DAY_MS, c, c + 0.1, c - 0.1, c, 100.0, True, "test")


def rising_daily(n: int = 40) -> list[Bar]:
    return [bday(i, 1.0 + i * 0.05) for i in range(n)]


def falling_daily(n: int = 40) -> list[Bar]:
    return [bday(i, 10.0 - i * 0.05) for i in range(n)]


def test_locked_params():
    assert SPOT_MD == "BTC-USDT"
    assert BAR == "1H"
    assert FAST == 12 and SLOW == 30
    assert SCALP_START_EUR == 20.0
    assert SCALP_DD_ABS_CAP_EUR == 10.0
    assert BH_DD_MULT == 1.10
    assert TIM_HIGH == 0.80
    assert FAMILY == "ema12_30_long_flat_1h_daily_bull"
    assert GATE_NAME == "core_style_return"
    assert SOURCE == "scalp_btc_ema_1h"
    assert DIFFERS_FROM_HOLDOUT_EXP_GATE is True
    assert "thin" in DIFFERS_REASON.lower() or "fragile" in DIFFERS_REASON.lower()
    assert "#36" in PRIOR_HOLDOUT_EXP_TRIALS and "#44" in PRIOR_HOLDOUT_EXP_TRIALS
    assert "#41" not in PRIOR_HOLDOUT_EXP_TRIALS
    assert "#45" not in PRIOR_HOLDOUT_EXP_TRIALS
    assert "#46" not in PRIOR_HOLDOUT_EXP_TRIALS
    assert "#48" not in PRIOR_HOLDOUT_EXP_TRIALS
    assert "#50" not in PRIOR_HOLDOUT_EXP_TRIALS


def test_strategy_never_short_and_label():
    strat = ScalpBtcEma1hV1(ScalpBtcEma1hParams(fast=12, slow=30), daily_bars=rising_daily())
    assert strat.label.startswith("scalp_btc_ema_1h")
    assert "bull_on" in strat.label
    assert strat.desired_state([]) == FLAT
    assert strat.warmup_bars() == 30
    assert strat.params.daily_bull_filter is True


def test_daily_bull_true_on_rising_false_on_falling():
    rising = rising_daily()
    falling = falling_daily()
    asof = rising[-1].ts_close_ms + 1000
    s_bull = ScalpBtcEma1hV1(daily_bars=rising)
    s_bear = ScalpBtcEma1hV1(daily_bars=falling)
    assert s_bull.daily_bull(asof) is True
    assert s_bear.daily_bull(asof) is False


def test_entry_gate_blocks_new_long_when_daily_bear():
    """1H EMA long but daily bear → stay flat (no new long)."""
    # Rising 1H so EMA12>EMA30 after warmup
    bars = [b1h(i, 1.0 + i * 0.02) for i in range(80)]
    falling = falling_daily()
    # Align daily timestamps before 1H bars
    last_1h = bars[-1].ts_close_ms
    daily = []
    for i in range(40):
        ts = last_1h - (40 - i) * DAY_MS
        px = 10.0 - i * 0.05
        daily.append(Bar("BTC-USDT", ts, ts + DAY_MS, px, px + 0.01, px - 0.01, px, 1.0, True, "test"))
    strat = ScalpBtcEma1hV1(daily_bars=daily)
    settings = EmaBookSettings(equity_eur=20.0, fee_rate=0.0005, slippage_bps=5.0)
    walk = walk_long_flat_1h_daily_bull(
        bars,
        strategy=strat,
        settings=settings,
        trade_start_ms=bars[40].ts_open_ms,
        trade_end_ms=bars[-1].ts_open_ms + BAR_MS,
    )
    assert walk["n_entries"] == 0
    assert walk["n_blocked_by_daily_bull"] > 0
    assert walk["n_short_signals"] == 0


def test_entry_gate_allows_long_when_daily_bull():
    bars = [b1h(i, 1.0 + i * 0.02) for i in range(80)]
    last_1h = bars[-1].ts_close_ms
    daily = []
    for i in range(40):
        ts = last_1h - (40 - i) * DAY_MS
        px = 1.0 + i * 0.05
        daily.append(Bar("BTC-USDT", ts, ts + DAY_MS, px, px + 0.01, px - 0.01, px, 1.0, True, "test"))
    strat = ScalpBtcEma1hV1(daily_bars=daily)
    settings = EmaBookSettings(equity_eur=20.0, fee_rate=0.0005, slippage_bps=5.0)
    walk = walk_long_flat_1h_daily_bull(
        bars,
        strategy=strat,
        settings=settings,
        trade_start_ms=bars[40].ts_open_ms,
        trade_end_ms=bars[-1].ts_open_ms + BAR_MS,
    )
    assert walk["n_entries"] >= 1
    assert walk["n_short_signals"] == 0
    assert walk["time_in_market"] is not None and walk["time_in_market"] > 0


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


def test_score_scalp_dd_vs_bh_fail():
    full = {
        "ok": True,
        "n_trades": 1,
        "net_return_eur": 1.5,
        "max_dd_eur": 12.0,
        "bh_max_dd_eur": 10.0,  # 12 > 11 → fail
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
        "net_return_eur": 0.3,
        "max_dd_eur": 0.5,
        "bh_max_dd_eur": None,
        "time_in_market": 0.3,
        "expectancy_after_costs_eur": 0.3,
    }
    sc = score_scalp(full, hold)
    assert sc["full_pass"] is True  # 9 <= 10
    assert sc["holdout_ok_if_full_passed"] is True


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
        "max_dd_eur": 0.2,
        "bh_max_dd_eur": 0.2,
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
        "net_return_eur": -0.3,
        "max_dd_eur": 0.5,
        "bh_max_dd_eur": 0.5,
        "time_in_market": 0.4,
        "expectancy_after_costs_eur": -0.3,
    }
    sc = score_scalp(full, hold)
    assert sc["full_pass"] is True
    assert sc["holdout_ok_if_full_passed"] is False


def test_aggregate_requires_two_clean():
    def _wr(wid: str, *, full_pass: bool, hold_ok: bool | None, n: int, tim: float = 1.0) -> dict:
        return {
            "window_id": wid,
            "scalp": {
                "full": {
                    "n_trades": n,
                    "ok": True,
                    "time_in_market": tim,
                    "expectancy_after_costs_eur": 0.1 if n else None,
                },
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
        "expectancy_after_costs_eur": 0.2,
    }
    sc = score_scalp(full, None)
    assert sc["gate_mode"] == "core_style_return"
    assert sc["full_pass"] is False
    assert sc["full_net_return_gt_0"] is False
