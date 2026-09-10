"""Unit tests: Mid DOGE RSI(14) MR — holdout-exp gate like #36."""

from __future__ import annotations

import pytest

from atlas.paper.engine import PaperEngine, PaperSettings
from atlas.paper.eval import NullJournal
from atlas.paper.mid_doge_rsi_mr_eval import (
    LOW_FREQ_MEDIAN_CAP,
    MID_DD_CAP_EUR,
    SPOT_MD,
    aggregate_set,
    score_mid,
)
from atlas.paper.types import Bar, Side
from atlas.strategy.mid_doge_rsi_mr import (
    ENTRY_RSI,
    EXIT_RSI,
    RSI_PERIOD,
    TIME_STOP_BARS,
    MidDogeRsiMrParams,
    MidDogeRsiMrV1,
    TradeWindowGate,
    rsi_wilder,
)

DAY_MS = 86_400_000
EPOCH = 1_700_000_000_000
SYM = "DOGE-USDT"


def _daily(symbol: str, i: int, close: float, *, high: float | None = None, low: float | None = None) -> Bar:
    open_ms = EPOCH + i * DAY_MS
    o = close
    h = high if high is not None else close * 1.01
    l = low if low is not None else close * 0.99
    return Bar(
        symbol=symbol,
        ts_open_ms=open_ms,
        ts_close_ms=open_ms + DAY_MS,
        open=o,
        high=max(h, o, close),
        low=min(l, o, close),
        close=close,
        volume=1e6,
        closed=True,
        source="test",
    )


def _build_oversold_series() -> list[Bar]:
    """Steady then sharp dump so Wilder RSI(14) drops below 30; prior-14 low usable."""
    bars: list[Bar] = []
    px = 0.20
    for i in range(30):
        px = px * 1.005
        bars.append(_daily(SYM, i, px, high=px * 1.01, low=px * 0.99))
    # Sharp multi-day dump to force RSI < 30
    for j in range(18):
        i = 30 + j
        px = px * 0.92
        bars.append(_daily(SYM, i, px, high=px * 1.005, low=px * 0.97))
    return bars


def test_spot_md_and_locked_constants():
    assert SPOT_MD == "DOGE-USDT"
    assert MID_DD_CAP_EUR == 16.0
    assert LOW_FREQ_MEDIAN_CAP == 15
    assert RSI_PERIOD == 14
    assert ENTRY_RSI == 30.0
    assert EXIT_RSI == 50.0
    assert TIME_STOP_BARS >= 10**6  # inert — no time stop in hyp


def test_rsi_wilder_known_shape():
    closes = [float(i) for i in range(1, 40)]
    s = rsi_wilder(closes, 14)
    assert s[13] is None  # first RSI at index period
    assert s[14] is not None
    assert 0.0 <= float(s[14]) <= 100.0
    # Monotonic uptrend → RSI high
    assert float(s[-1]) > 70.0


def test_no_ema_in_params_or_label():
    p = MidDogeRsiMrParams()
    assert not hasattr(p, "ema_fast")
    strat = MidDogeRsiMrV1()
    assert "ema" not in strat.label.lower()
    assert "rsi" in strat.label.lower()


def test_entry_when_rsi_below_30():
    bars = _build_oversold_series()
    strat = MidDogeRsiMrV1()
    closes = [float(b.close) for b in bars]
    rsi = rsi_wilder(closes, 14)[-1]
    assert rsi is not None and float(rsi) < 30.0
    sig = strat.on_closed_bar(bars)
    assert sig is not None
    assert sig.side is Side.LONG
    assert sig.symbol == SYM
    assert sig.reason == "mid_doge_rsi_mr_oversold"
    assert sig.extras["atr_stop"] is False
    assert sig.extras["time_stop"] is False
    assert sig.extras["rsi"] < 30.0
    assert sig.stop < bars[-1].close
    assert float(sig.extras.get("take_profit") or 0.0) == 0.0


def test_no_entry_when_rsi_not_oversold():
    bars: list[Bar] = []
    px = 0.10
    for i in range(40):
        px = px * 1.01
        bars.append(_daily(SYM, i, px))
    assert MidDogeRsiMrV1().on_closed_bar(bars) is None


def test_no_short_ever():
    bars = _build_oversold_series()
    sig = MidDogeRsiMrV1().on_closed_bar(bars)
    assert sig is None or sig.side is Side.LONG


def test_exit_hint_rsi_above_50():
    bars = _build_oversold_series()
    strat = MidDogeRsiMrV1()
    # Rally hard so RSI recovers above 50
    px = bars[-1].close
    for j in range(25):
        px = px * 1.08
        bars.append(_daily(SYM, len(bars), px, high=px * 1.01, low=px * 0.99))
    closes = [float(b.close) for b in bars]
    rsi = rsi_wilder(closes, 14)[-1]
    assert rsi is not None and float(rsi) > 50.0
    hint = strat.exit_hint(Side.LONG, bars)
    assert hint == "rsi_exit"
    # Flat side → no hint
    assert strat.exit_hint(Side.SHORT, bars) is None


def test_trade_window_gate_blocks_outside():
    bars = _build_oversold_series()
    inner = MidDogeRsiMrV1()
    gate = TradeWindowGate(inner, trade_start_ms=bars[0].ts_open_ms, trade_end_ms=bars[-1].ts_open_ms)
    assert gate.on_closed_bar(bars) is None
    gate2 = TradeWindowGate(
        inner,
        trade_start_ms=bars[0].ts_open_ms,
        trade_end_ms=bars[-1].ts_close_ms + 1,
    )
    assert gate2.on_closed_bar(bars) is not None


def test_score_mid_holdout_not_worse_than_full():
    full = {
        "ok": True,
        "expectancy_after_costs_eur": 0.50,
        "max_dd_eur": 1.0,
        "n_trades": 4,
    }
    hold_ok = {"ok": True, "expectancy_after_costs_eur": 0.50, "n_trades": 1, "max_dd_eur": 0.5}
    sc = score_mid(full, hold_ok, dd_cap_eur=16.0)
    assert sc["full_pass"] is True
    assert sc["holdout_ok_if_full_passed"] is True
    assert sc["gate_mode"] == "holdout_exp_mid_like_36"

    hold_better = {"ok": True, "expectancy_after_costs_eur": 0.80, "n_trades": 1, "max_dd_eur": 0.5}
    assert score_mid(full, hold_better, dd_cap_eur=16.0)["holdout_ok_if_full_passed"] is True

    hold_worse = {"ok": True, "expectancy_after_costs_eur": 0.10, "n_trades": 1, "max_dd_eur": 0.5}
    assert score_mid(full, hold_worse, dd_cap_eur=16.0)["holdout_ok_if_full_passed"] is False

    hold_zero_n = {"ok": True, "expectancy_after_costs_eur": 1.0, "n_trades": 0, "max_dd_eur": 0.5}
    assert score_mid(full, hold_zero_n, dd_cap_eur=16.0)["holdout_ok_if_full_passed"] is False


def test_aggregate_low_freq_is_flag_not_hard_gate():
    def _wr(wid: str, n: int, *, hold_ok: bool = True) -> dict:
        return {
            "window_id": wid,
            "mid": {
                "full": {"n_trades": n, "ok": True, "expectancy_after_costs_eur": 0.2, "max_dd_eur": 1.0},
                "score": {
                    "missing_or_nan": False,
                    "full_expectancy_gt_0": True,
                    "full_dd_within_cap": True,
                    "full_pass": True,
                    "holdout_ok_if_full_passed": hold_ok,
                },
            },
        }

    ok = aggregate_set([_wr("A1", 2), _wr("A2", 3), _wr("A3", 1)])
    assert ok["verdict"] == "PASS"
    assert ok["mid"]["low_freq_is_pass_gate"] is False

    many = aggregate_set([_wr("A1", 20), _wr("A2", 22), _wr("A3", 18)])
    assert many["verdict"] == "PASS"
    assert many["mid"]["low_freq_ok"] is False
    assert many["mid"]["low_freq_flag"] is True

    hold_fail = aggregate_set([_wr("A1", 2, hold_ok=False), _wr("A2", 3), _wr("A3", 1)])
    assert hold_fail["verdict"] == "FAIL"


def test_engine_roundtrip_rsi_exit_no_atr_tp():
    bars = _build_oversold_series()
    # Confirm entry exists, then rally for RSI exit room
    strat = MidDogeRsiMrV1()
    sig = strat.on_closed_bar(bars)
    assert sig is not None
    px = bars[-1].close
    for j in range(30):
        px = px * 1.06
        bars.append(_daily(SYM, len(bars), px))

    settings = PaperSettings(
        equity_eur=40.0,
        per_trade_risk_frac=0.015,
        daily_kill_frac=0.05,
        one_position=True,
        time_stop_bars=TIME_STOP_BARS,
        leverage_default=1.0,
        leverage_hard_cap=1.0,
        fee_rate=0.0005,
        slippage_bps=5.0,
    )
    eng = PaperEngine(settings, strat, journal=NullJournal(), run_id="test-doge-rsi-mr", data_dir="data")
    paper = eng.run({SYM: bars}, {SYM: []}, universe=[SYM])
    assert paper.n_entries >= 1
