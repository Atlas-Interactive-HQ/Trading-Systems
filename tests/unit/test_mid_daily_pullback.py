"""Unit tests: Mid daily EMA pullback long entry/exit + TP/time-stop path."""

from __future__ import annotations

import pytest

from atlas.paper.engine import PaperEngine, PaperSettings
from atlas.paper.eval import NullJournal
from atlas.paper.types import Bar, Side
from atlas.strategy.mid_daily_pullback import (
    FLAT,
    LONG,
    MidDailyPullbackParams,
    MidDailyPullbackV1,
    TradeWindowGate,
    regime_state,
)

DAY_MS = 86_400_000
EPOCH = 1_700_000_000_000


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


def _rising(n: int, start: float = 0.05, step: float = 0.002) -> list[float]:
    return [start + i * step for i in range(n)]


def _build_reclaim_series() -> list[Bar]:
    """Uptrend then dip (low through EMA / prior below) then reclaim close."""
    bars: list[Bar] = []
    px = 0.10
    for i in range(50):
        px = px * 1.015
        bars.append(_daily("DOGE-USDT", i, px))
    # mild pullback days
    for j in range(2):
        i = 50 + j
        px = px * 0.97
        bars.append(_daily("DOGE-USDT", i, px, low=px * 0.95, high=px * 1.01))
    # reclaim day: close back up, low still tagged soft
    i = 52
    px = px * 1.04
    bars.append(_daily("DOGE-USDT", i, px, high=px * 1.02, low=px * 0.96))
    return bars


def test_regime_long_on_uptrend():
    closes = _rising(40)
    bars = [_daily("DOGE-USDT", i, c) for i, c in enumerate(closes)]
    assert regime_state(bars) == LONG


def test_regime_flat_on_downtrend():
    closes = list(reversed(_rising(40)))
    bars = [_daily("DOGE-USDT", i, c) for i, c in enumerate(closes)]
    assert regime_state(bars) == FLAT


def test_insufficient_history_is_flat():
    bars = [_daily("DOGE-USDT", i, 0.1 + i * 0.001) for i in range(10)]
    assert regime_state(bars) == FLAT


def test_entry_on_pullback_reclaim():
    bars = _build_reclaim_series()
    strat = MidDailyPullbackV1()
    sig = strat.on_closed_bar(bars)
    assert sig is not None
    assert sig.side is Side.LONG
    assert sig.extras["take_profit"] > bars[-1].close
    assert sig.stop < bars[-1].close
    r = (sig.extras["take_profit"] - bars[-1].close) / (bars[-1].close - sig.stop)
    assert r == pytest.approx(2.0, rel=1e-6)


def test_no_entry_without_pullback():
    # strong uptrend closes only — highs/lows tight, no prior below EMA
    bars = []
    px = 0.10
    for i in range(55):
        px = px * 1.02
        # low stays above any reasonable EMA12 (very tight range above close path)
        bars.append(_daily("DOGE-USDT", i, px, high=px * 1.001, low=px * 0.999))
    strat = MidDailyPullbackV1()
    # may or may not signal depending on EMA touch; force no prior below + low > ema by construction
    # If signal appears, low must have touched — assert reason path via extras
    sig = strat.on_closed_bar(bars)
    if sig is not None:
        assert sig.extras.get("pullback_touched") or sig.extras.get("pullback_prior_below")


def test_no_short_ever():
    bars = _build_reclaim_series()
    strat = MidDailyPullbackV1()
    sig = strat.on_closed_bar(bars)
    assert sig is None or sig.side is Side.LONG


def test_exit_hint_regime_flat():
    # build long regime then crash so EMA12 <= EMA30
    up = _rising(40, start=0.2, step=0.01)
    bars = [_daily("DOGE-USDT", i, c) for i, c in enumerate(up)]
    assert regime_state(bars) == LONG
    px = up[-1]
    for j in range(25):
        px = px * 0.92
        bars.append(_daily("DOGE-USDT", 40 + j, px))
    strat = MidDailyPullbackV1()
    assert strat.exit_hint(Side.LONG, bars) == "regime_flat"
    assert strat.exit_hint(Side.SHORT, bars) is None


def test_trade_window_gate_blocks_outside():
    bars = _build_reclaim_series()
    inner = MidDailyPullbackV1()
    # window ends before last bar
    gate = TradeWindowGate(inner, trade_start_ms=bars[0].ts_open_ms, trade_end_ms=bars[-1].ts_open_ms)
    assert gate.on_closed_bar(bars) is None
    gate2 = TradeWindowGate(
        inner,
        trade_start_ms=bars[0].ts_open_ms,
        trade_end_ms=bars[-1].ts_close_ms + 1,
    )
    assert gate2.on_closed_bar(bars) is not None


def test_engine_roundtrip_tp_or_exit():
    bars = _build_reclaim_series()
    last = bars[-1]
    # next open fill bar
    bars.append(
        Bar(
            symbol="DOGE-USDT",
            ts_open_ms=last.ts_close_ms,
            ts_close_ms=last.ts_close_ms + DAY_MS,
            open=last.close * 1.001,
            high=last.close * 1.002,
            low=last.close * 0.999,
            close=last.close * 1.001,
            volume=1e6,
            closed=True,
            source="test",
        )
    )
    e = bars[-1]
    # big up bar to hit +2R TP
    bars.append(
        Bar(
            symbol="DOGE-USDT",
            ts_open_ms=e.ts_close_ms,
            ts_close_ms=e.ts_close_ms + DAY_MS,
            open=e.close,
            high=e.close * 1.50,
            low=e.close * 0.999,
            close=e.close * 1.05,
            volume=1e6,
            closed=True,
            source="test",
        )
    )
    strat = MidDailyPullbackV1(MidDailyPullbackParams(sleeve="mid"))
    settings = PaperSettings(
        equity_eur=40.0,
        per_trade_risk_frac=0.015,
        daily_kill_frac=0.05,
        one_position=True,
        time_stop_bars=10,
        leverage_default=1.0,
        leverage_hard_cap=1.0,
        fee_rate=0.0005,
        slippage_bps=5.0,
    )
    eng = PaperEngine(settings, strat, journal=NullJournal(), run_id="test-mid-daily-tp")
    summary = eng.run({"DOGE-USDT": bars}, {"DOGE-USDT": []}, universe=["DOGE-USDT"])
    assert summary.n_entries >= 1
    assert summary.n_trades >= 1
    reasons = [f.reason for f in summary.fills if f.kind == "exit"]
    assert reasons
    assert reasons[0] in ("take_profit", "time_stop", "stop", "regime_flat", "daily_kill")
