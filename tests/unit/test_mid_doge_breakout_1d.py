"""Unit tests: Mid DOGE BreakoutV1 1D + same-bar EMA bull Core-style RETURN (#47)."""

from __future__ import annotations

from atlas.paper.cascade import MID_START_EUR
from atlas.paper.mid_doge_breakout_1d_eval import (
    ATR_STOP_MULT,
    BAR,
    BH_DD_MULT,
    DIFFERS_FROM_HOLDOUT_EXP_GATE,
    DIFFERS_REASON,
    FAMILY,
    GATE_NAME,
    MID_DD_ABS_CAP_EUR,
    PRIOR_HOLDOUT_EXP_TRIALS,
    SOURCE,
    SPOT_MD,
    TIM_HIGH,
    aggregate_set,
    score_mid,
)
from atlas.paper.types import Bar, Side
from atlas.strategy.breakout import BreakoutParams, BreakoutV1
from atlas.strategy.mid_doge_breakout_1d import (
    MidDogeBreakout1dParams,
    MidDogeBreakout1dV1,
    same_bar_ema_bull,
)

DAY_MS = 24 * 60 * 60 * 1000
START = 1_700_000_000_000


def bday(i: int, o: float, h: float, l: float, c: float, symbol="DOGE-USDT") -> Bar:
    ts = START + i * DAY_MS
    return Bar(symbol, ts, ts + DAY_MS, o, h, l, c, 100.0, True, "test")


def make_flat(n: int) -> list[Bar]:
    return [bday(i, 100.0, 100.4, 99.6, 100.0) for i in range(n)]


def rising_closes(n: int = 40) -> list[Bar]:
    return [bday(i, 1.0 + i * 0.05, 1.0 + i * 0.05 + 0.02, 1.0 + i * 0.05 - 0.02, 1.0 + i * 0.05) for i in range(n)]


def falling_closes(n: int = 40) -> list[Bar]:
    return [bday(i, 10.0 - i * 0.05, 10.0 - i * 0.05 + 0.02, 10.0 - i * 0.05 - 0.02, 10.0 - i * 0.05) for i in range(n)]


def test_locked_params():
    assert SPOT_MD == "DOGE-USDT"
    assert BAR == "1D"
    assert MID_START_EUR == 40.0
    assert MID_DD_ABS_CAP_EUR == 20.0
    assert BH_DD_MULT == 1.10
    assert TIM_HIGH == 0.80
    assert ATR_STOP_MULT == 1.5
    assert FAMILY == "breakout_v1_long_bull_ema12_30_1d"
    assert GATE_NAME == "core_style_return"
    assert SOURCE == "mid_doge_breakout_1d"
    assert DIFFERS_FROM_HOLDOUT_EXP_GATE is True
    assert "thin" in DIFFERS_REASON.lower() or "fragile" in DIFFERS_REASON.lower()
    assert "#36" in PRIOR_HOLDOUT_EXP_TRIALS and "#44" in PRIOR_HOLDOUT_EXP_TRIALS
    assert "#41" not in PRIOR_HOLDOUT_EXP_TRIALS
    assert "#45" not in PRIOR_HOLDOUT_EXP_TRIALS


def test_oneh_must_be_off():
    try:
        MidDogeBreakout1dV1(MidDogeBreakout1dParams(oneh_filter="stub"))
        assert False, "expected ValueError"
    except ValueError as e:
        assert "oneh_filter" in str(e)


def test_long_only_drops_short():
    inner = BreakoutV1(BreakoutParams(lookback_15m=4, atr_period=3, oneh_filter="off", min_atr_frac=0.0))
    bars = make_flat(8) + [bday(8, 100.0, 100.0, 96.0, 96.0)]
    assert inner.on_closed_bar(bars) is not None
    assert inner.on_closed_bar(bars).side is Side.SHORT

    # Rising EMA path so bull gate would pass; short still dropped.
    base = rising_closes(40)
    # Replace last few with a down-break relative to prior highs while keeping uptrend EMAs
    # Simpler: use rising for bull, then force short via flat+drop on a short series with bull EMAs separate.
    strat = MidDogeBreakout1dV1(
        MidDogeBreakout1dParams(lookback=4, atr_period=3, min_atr_frac=0.0, atr_stop_mult=1.5)
    )
    # Build bars: rising for EMA, then a down break that Breakout would short
    bars = rising_closes(35)
    # Append flat then break down below prior 4-bar low
    for i in range(5):
        px = bars[-1].close
        bars.append(bday(35 + i, px, px + 0.01, px - 0.01, px))
    # Down break
    last_i = len(bars)
    low = min(b.low for b in bars[-5:-1])
    bars.append(bday(last_i, low, low + 0.01, low - 0.5, low - 0.4))
    # If inner would short, wrapper must return None
    inner2 = BreakoutV1(BreakoutParams(lookback_15m=4, atr_period=3, oneh_filter="off", min_atr_frac=0.0))
    sig_inner = inner2.on_closed_bar(bars)
    if sig_inner is not None and sig_inner.side is Side.SHORT:
        assert strat.on_closed_bar(bars) is None


def test_bull_filter_blocks_when_bear():
    strat = MidDogeBreakout1dV1(
        MidDogeBreakout1dParams(lookback=4, atr_period=3, min_atr_frac=0.0)
    )
    bars = falling_closes(40)
    # Force a would-be long breakout: raise last close above prior 4 high
    prior_high = max(b.high for b in bars[-5:-1])
    bars[-1] = bday(39, prior_high, prior_high + 1.0, prior_high - 0.1, prior_high + 0.8)
    assert same_bar_ema_bull(bars) != "long"
    assert strat.on_closed_bar(bars) is None


def test_bull_filter_allows_long_in_bull():
    strat = MidDogeBreakout1dV1(
        MidDogeBreakout1dParams(lookback=4, atr_period=3, min_atr_frac=0.0)
    )
    bars = rising_closes(40)
    prior_high = max(b.high for b in bars[-5:-1])
    bars[-1] = bday(39, prior_high, prior_high + 1.0, prior_high - 0.1, prior_high + 0.8)
    assert same_bar_ema_bull(bars) == "long"
    sig = strat.on_closed_bar(bars)
    assert sig is not None
    assert sig.side is Side.LONG
    assert "bull_ema" in sig.reason
    assert "same_bar" in sig.reason


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
    sc = score_mid(full, hold)
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
    sc = score_mid(full, None)
    assert sc["full_pass"] is False
    assert sc["full_dd_within_cap"] is False


def test_score_abs_dd_cap_mid20():
    full = {
        "ok": True,
        "n_trades": 1,
        "net_return_eur": 1.0,
        "max_dd_eur": 18.0,
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
    sc = score_mid(full, hold)
    assert sc["full_pass"] is True  # 18 <= 20
    assert sc["holdout_ok_if_full_passed"] is True


def test_score_holdout_zero_trade_low_tim_fail():
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


def test_aggregate_needs_two_clean():
    def wr(wid, full_pass, hold_ok, n=2, net=1.0, dd=1.0, exp=0.5, tim=0.2):
        return {
            "window_id": wid,
            "mid": {
                "full": {
                    "ok": True,
                    "n_trades": n,
                    "net_return_eur": net,
                    "max_dd_eur": dd,
                    "time_in_market": tim,
                    "expectancy_after_costs_eur": exp,
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

    agg = aggregate_set([wr("A1", True, True), wr("A2", True, False), wr("A3", False, None)])
    assert agg["verdict"] == "FAIL"  # only 1 clean
    assert agg["mid"]["clean_pass_windows"] == ["A1"]

    agg2 = aggregate_set([wr("A1", True, True), wr("A2", True, True), wr("A3", False, None)])
    assert agg2["verdict"] == "PASS"
    assert set(agg2["mid"]["clean_pass_windows"]) == {"A1", "A2"}
