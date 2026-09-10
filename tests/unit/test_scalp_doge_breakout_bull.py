"""Unit tests: Scalp DOGE BreakoutV1 long+bull Core-style RETURN gate (#46)."""

from __future__ import annotations

from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.scalp_doge_breakout_bull_eval import (
    ATR_STOP_MULT,
    BH_DD_MULT,
    DIFFERS_FROM_HOLDOUT_EXP_GATE,
    FAMILY,
    GATE_NAME,
    PRIOR_HOLDOUT_EXP_TRIALS,
    SCALP_DD_ABS_CAP_EUR,
    SOURCE,
    SPOT_MD,
    TIM_HIGH,
    aggregate_set,
    score_scalp,
)
from atlas.paper.types import Bar, Side
from atlas.strategy.breakout import BreakoutParams, BreakoutV1
from atlas.strategy.scalp_doge_breakout_bull import (
    ScalpDogeBreakoutBullParams,
    ScalpDogeBreakoutBullV1,
)

BAR_MS = 15 * 60 * 1000
DAY_MS = 24 * 60 * 60 * 1000
START = 1_700_000_000_000


def b15(i: int, o: float, h: float, l: float, c: float, symbol="DOGE-USDT") -> Bar:
    ts = START + i * BAR_MS
    return Bar(symbol, ts, ts + BAR_MS, o, h, l, c, 10.0, True, "test")


def bday(i: int, c: float, symbol="DOGE-USDT") -> Bar:
    ts = START + i * DAY_MS
    return Bar(symbol, ts, ts + DAY_MS, c, c + 0.1, c - 0.1, c, 100.0, True, "test")


def make_flat(n: int) -> list[Bar]:
    return [b15(i, 100.0, 100.4, 99.6, 100.0) for i in range(n)]


def rising_daily(n: int = 40) -> list[Bar]:
    # Rising closes so EMA12 > EMA30 after warmup.
    return [bday(i, 1.0 + i * 0.05) for i in range(n)]


def falling_daily(n: int = 40) -> list[Bar]:
    return [bday(i, 10.0 - i * 0.05) for i in range(n)]


def test_locked_params():
    assert SPOT_MD == "DOGE-USDT"
    assert SCALP_START_EUR == 20.0
    assert SCALP_DD_ABS_CAP_EUR == 10.0
    assert BH_DD_MULT == 1.10
    assert TIM_HIGH == 0.80
    assert ATR_STOP_MULT == 1.5
    assert FAMILY == "breakout_v1_long_bull_ema12_30"
    assert GATE_NAME == "core_style_return"
    assert SOURCE == "scalp_doge_breakout_bull"
    assert DIFFERS_FROM_HOLDOUT_EXP_GATE is True
    assert "#36" in PRIOR_HOLDOUT_EXP_TRIALS and "#40" in PRIOR_HOLDOUT_EXP_TRIALS


def test_long_only_drops_short():
    inner = BreakoutV1(BreakoutParams(lookback_15m=4, atr_period=3, oneh_filter="off", min_atr_frac=0.0))
    bars = make_flat(8) + [b15(8, 100.0, 100.0, 96.0, 96.0)]
    assert inner.on_closed_bar(bars) is not None
    assert inner.on_closed_bar(bars).side is Side.SHORT

    strat = ScalpDogeBreakoutBullV1(
        ScalpDogeBreakoutBullParams(
            lookback_15m=4,
            atr_period=3,
            oneh_filter="off",
            min_atr_frac=0.0,
            atr_stop_mult=1.5,
        ),
        daily_bars=rising_daily(),
    )
    # Align daily close ts after last 15m bar.
    last_ts = bars[-1].ts_close_ms
    daily = []
    for i in range(40):
        ts = last_ts - (40 - i) * DAY_MS
        px = 1.0 + i * 0.05
        daily.append(Bar("DOGE-USDT", ts, ts + DAY_MS, px, px + 0.01, px - 0.01, px, 1.0, True, "test"))
    strat.set_daily_bars(daily)
    assert strat.on_closed_bar(bars) is None  # short dropped


def test_bull_filter_blocks_when_bear():
    strat = ScalpDogeBreakoutBullV1(
        ScalpDogeBreakoutBullParams(
            lookback_15m=4,
            atr_period=3,
            oneh_filter="off",
            min_atr_frac=0.0,
        ),
    )
    bars = make_flat(8) + [b15(8, 100.0, 104.0, 100.0, 104.0)]
    last_ts = bars[-1].ts_close_ms
    daily = []
    for i in range(40):
        ts = last_ts - (40 - i) * DAY_MS
        px = 10.0 - i * 0.05
        daily.append(Bar("DOGE-USDT", ts, ts + DAY_MS, px, px + 0.01, px - 0.01, px, 1.0, True, "test"))
    strat.set_daily_bars(daily)
    assert strat.on_closed_bar(bars) is None


def test_bull_filter_allows_long_in_bull():
    strat = ScalpDogeBreakoutBullV1(
        ScalpDogeBreakoutBullParams(
            lookback_15m=4,
            atr_period=3,
            oneh_filter="off",
            min_atr_frac=0.0,
        ),
    )
    bars = make_flat(8) + [b15(8, 100.0, 104.0, 100.0, 104.0)]
    last_ts = bars[-1].ts_close_ms
    daily = []
    for i in range(40):
        ts = last_ts - (40 - i) * DAY_MS
        px = 1.0 + i * 0.05
        daily.append(Bar("DOGE-USDT", ts, ts + DAY_MS, px, px + 0.01, px - 0.01, px, 1.0, True, "test"))
    strat.set_daily_bars(daily)
    sig = strat.on_closed_bar(bars)
    assert sig is not None
    assert sig.side is Side.LONG
    assert "bull_ema" in sig.reason


def test_score_return_pass_with_bh_dd():
    full = {
        "ok": True,
        "n_trades": 2,
        "net_return_eur": 1.5,
        "max_dd_eur": 2.0,
        "bh_max_dd_eur": 2.0,
        "time_in_market": 0.2,
        "expectancy_after_costs_eur": 0.75,
    }
    hold = {
        "ok": True,
        "n_trades": 1,
        "net_return_eur": 0.3,
        "max_dd_eur": 0.5,
        "bh_max_dd_eur": 0.5,
        "time_in_market": 0.1,
        "expectancy_after_costs_eur": 0.3,
    }
    sc = score_scalp(full, hold)
    assert sc["gate_mode"] == "core_style_return"
    assert sc["differs_from_holdout_exp_gate"] is True
    assert sc["full_pass"] is True
    assert sc["holdout_ok_if_full_passed"] is True
    assert sc["full_expectancy_after_costs_eur"] == 0.75


def test_score_dd_vs_bh_fail():
    full = {
        "ok": True,
        "n_trades": 1,
        "net_return_eur": 1.0,
        "max_dd_eur": 12.0,
        "bh_max_dd_eur": 10.0,  # 12 > 11
        "time_in_market": 0.2,
        "expectancy_after_costs_eur": 1.0,
    }
    sc = score_scalp(full, None)
    assert sc["full_pass"] is False
    assert sc["full_dd_within_cap"] is False


def test_score_abs_dd_cap_scalp10():
    full = {
        "ok": True,
        "n_trades": 1,
        "net_return_eur": 1.0,
        "max_dd_eur": 9.5,
        "bh_max_dd_eur": None,
        "time_in_market": 0.2,
        "expectancy_after_costs_eur": 1.0,
    }
    hold = {
        "ok": True,
        "n_trades": 1,
        "net_return_eur": 0.2,
        "max_dd_eur": 1.0,
        "bh_max_dd_eur": None,
        "time_in_market": 0.1,
        "expectancy_after_costs_eur": 0.2,
    }
    sc = score_scalp(full, hold)
    assert sc["full_pass"] is True
    full["max_dd_eur"] = 10.5
    sc2 = score_scalp(full, hold)
    assert sc2["full_pass"] is False


def test_score_holdout_zero_trade_low_tim_fail():
    full = {
        "ok": True,
        "n_trades": 1,
        "net_return_eur": 1.0,
        "max_dd_eur": 1.0,
        "bh_max_dd_eur": 1.0,
        "time_in_market": 0.3,
        "expectancy_after_costs_eur": 1.0,
    }
    hold = {
        "ok": True,
        "n_trades": 0,
        "net_return_eur": 0.5,
        "max_dd_eur": 0.1,
        "bh_max_dd_eur": 0.1,
        "time_in_market": 0.1,
        "expectancy_after_costs_eur": None,
    }
    sc = score_scalp(full, hold)
    assert sc["full_pass"] is True
    assert sc["holdout_ok_if_full_passed"] is False


def test_aggregate_requires_two_clean():
    def _wr(wid: str, *, full_pass: bool, hold_ok: bool | None, n: int, tim: float = 0.2) -> dict:
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
            _wr("A1", full_pass=True, hold_ok=True, n=2),
            _wr("A2", full_pass=False, hold_ok=None, n=0),
            _wr("A3", full_pass=True, hold_ok=True, n=1),
        ]
    )
    assert ok["verdict"] == "PASS"
    assert ok["scalp"]["pass"] is True
    assert ok["scalp"]["differs_from_holdout_exp_gate"] is True

    bad = aggregate_set(
        [
            _wr("A1", full_pass=True, hold_ok=True, n=2),
            _wr("A2", full_pass=True, hold_ok=False, n=1),
            _wr("A3", full_pass=False, hold_ok=None, n=0),
        ]
    )
    assert bad["verdict"] == "FAIL"
    assert bad["scalp"]["clean_pass_windows"] == ["A1"]
