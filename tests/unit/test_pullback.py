"""Unit tests: Mid/Scalp EMA pullback long entry/exit logic + TP fill."""

from __future__ import annotations

import pytest

from atlas.paper.engine import PaperEngine, PaperSettings
from atlas.paper.eval import NullJournal
from atlas.paper.fills import take_profit_hit_price
from atlas.paper.types import Bar, Side
from atlas.strategy.pullback import (
    FLAT,
    LONG,
    PullbackLongV1,
    PullbackParams,
    daily_regime_state,
)

DAY_MS = 86_400_000
BAR_MS = 15 * 60 * 1000
EPOCH = 1_700_000_000_000  # arbitrary UTC ms


def _bar(symbol: str, i: int, close: float, *, high: float | None = None, low: float | None = None) -> Bar:
    open_ms = EPOCH + i * BAR_MS
    o = close
    h = high if high is not None else close * 1.001
    l = low if low is not None else close * 0.999
    return Bar(
        symbol=symbol,
        ts_open_ms=open_ms,
        ts_close_ms=open_ms + BAR_MS,
        open=o,
        high=max(h, o, close),
        low=min(l, o, close),
        close=close,
        volume=1000.0,
        closed=True,
        source="test",
    )


def _daily_ending_at(symbol: str, n: int, end_close_ms: int, closes: list[float]) -> list[Bar]:
    """Build n daily bars whose last close equals end_close_ms."""
    assert len(closes) == n
    out: list[Bar] = []
    for i, close in enumerate(closes):
        # last bar (i=n-1) closes at end_close_ms
        ts_close = end_close_ms - (n - 1 - i) * DAY_MS
        ts_open = ts_close - DAY_MS
        out.append(
            Bar(
                symbol=symbol,
                ts_open_ms=ts_open,
                ts_close_ms=ts_close,
                open=close,
                high=close * 1.01,
                low=close * 0.99,
                close=close,
                volume=1e6,
                closed=True,
                source="test",
            )
        )
    return out


def _rising_closes(n: int, start: float = 0.05, step: float = 0.001) -> list[float]:
    return [start + i * step for i in range(n)]


def _flat_closes(n: int, px: float = 0.05) -> list[float]:
    return [px] * n


def _pullback_15m_series() -> list[Bar]:
    bars: list[Bar] = []
    px = 0.10
    for i in range(50):
        px = px * 1.002
        bars.append(_bar("DOGE-USDT", i, px))
    for j in range(3):
        i = 50 + j
        px = px * 0.985
        bars.append(_bar("DOGE-USDT", i, px, low=px * 0.99))
    i = 53
    px = px * 1.03
    bars.append(_bar("DOGE-USDT", i, px, high=px * 1.01, low=px * 0.99))
    return bars


def _daily_for_bars(bars: list[Bar], closes: list[float]) -> list[Bar]:
    # Prior closed daily available at decision: last daily closes at or before decision bar close.
    return _daily_ending_at("DOGE-USDT", len(closes), bars[-1].ts_close_ms, closes)


def test_daily_regime_long_on_uptrend():
    closes = _rising_closes(40)
    # synthetic end
    daily = _daily_ending_at("DOGE-USDT", 40, EPOCH + 40 * DAY_MS, closes)
    assert daily_regime_state(daily, asof_ts_ms=daily[-1].ts_close_ms) == LONG


def test_daily_regime_flat_on_equal_closes():
    closes = _flat_closes(40)
    daily = _daily_ending_at("DOGE-USDT", 40, EPOCH + 40 * DAY_MS, closes)
    assert daily_regime_state(daily, asof_ts_ms=daily[-1].ts_close_ms) == FLAT


def test_daily_regime_fail_closed_short_history():
    closes = _rising_closes(10)
    daily = _daily_ending_at("DOGE-USDT", 10, EPOCH + 10 * DAY_MS, closes)
    assert daily_regime_state(daily, asof_ts_ms=daily[-1].ts_close_ms) == FLAT


def test_entry_fires_on_reclaim_when_regime_long():
    bars = _pullback_15m_series()
    daily = _daily_for_bars(bars, _rising_closes(50))
    strat = PullbackLongV1(PullbackParams(sleeve="mid"), daily_bars=daily)
    sig = strat.on_closed_bar(bars)
    assert sig is not None
    assert sig.side is Side.LONG
    assert sig.stop < bars[-1].close
    assert sig.extras["take_profit"] > bars[-1].close
    stop_dist = bars[-1].close - sig.stop
    tp_dist = sig.extras["take_profit"] - bars[-1].close
    assert tp_dist == pytest.approx(2.0 * stop_dist, rel=1e-6)


def test_no_entry_when_regime_flat():
    bars = _pullback_15m_series()
    daily = _daily_for_bars(bars, _flat_closes(50))
    strat = PullbackLongV1(PullbackParams(sleeve="mid"), daily_bars=daily)
    assert strat.on_closed_bar(bars) is None


def test_no_entry_without_dip():
    bars = [_bar("DOGE-USDT", i, 0.10 * (1.002**i)) for i in range(54)]
    daily = _daily_for_bars(bars, _rising_closes(50))
    strat = PullbackLongV1(PullbackParams(sleeve="mid"), daily_bars=daily)
    assert strat.on_closed_bar(bars) is None


def test_exit_hint_regime_flat():
    bars = _pullback_15m_series()
    daily = _daily_for_bars(bars, _flat_closes(50))
    strat = PullbackLongV1(PullbackParams(sleeve="mid"), daily_bars=daily)
    assert strat.exit_hint(Side.LONG, bars) == "regime_flat"
    assert strat.exit_hint(Side.SHORT, bars) is None


def test_scalp_params_tighter_stop_and_1r_tp():
    bars = _pullback_15m_series()
    daily = _daily_for_bars(bars, _rising_closes(50))
    mid = PullbackLongV1(PullbackParams(atr_stop_mult=1.5, tp_r_multiple=2.0, sleeve="mid"), daily_bars=daily)
    scalp = PullbackLongV1(PullbackParams(atr_stop_mult=1.0, tp_r_multiple=1.0, sleeve="scalp"), daily_bars=daily)
    sm = mid.on_closed_bar(bars)
    ss = scalp.on_closed_bar(bars)
    assert sm is not None and ss is not None
    assert ss.stop > sm.stop
    mid_r = (sm.extras["take_profit"] - bars[-1].close) / (bars[-1].close - sm.stop)
    scalp_r = (ss.extras["take_profit"] - bars[-1].close) / (bars[-1].close - ss.stop)
    assert mid_r == pytest.approx(2.0, rel=1e-6)
    assert scalp_r == pytest.approx(1.0, rel=1e-6)


def test_take_profit_hit_price_long():
    b = _bar("X", 0, 100.0, high=110.0, low=99.0)
    assert take_profit_hit_price(Side.LONG, 105.0, b) == 105.0
    assert take_profit_hit_price(Side.LONG, 120.0, b) is None
    gap = _bar("X", 1, 112.0, high=113.0, low=111.0)
    assert take_profit_hit_price(Side.LONG, 105.0, gap) == 112.0


def test_engine_exits_after_entry():
    bars = _pullback_15m_series()
    last = bars[-1]
    bars.append(
        Bar(
            symbol="DOGE-USDT",
            ts_open_ms=last.ts_close_ms,
            ts_close_ms=last.ts_close_ms + BAR_MS,
            open=last.close * 1.001,
            high=last.close * 1.002,
            low=last.close * 0.999,
            close=last.close * 1.001,
            volume=1000.0,
            closed=True,
            source="test",
        )
    )
    e = bars[-1]
    bars.append(
        Bar(
            symbol="DOGE-USDT",
            ts_open_ms=e.ts_close_ms,
            ts_close_ms=e.ts_close_ms + BAR_MS,
            open=e.close,
            high=e.close * 1.20,
            low=e.close * 0.999,
            close=e.close * 1.01,
            volume=1000.0,
            closed=True,
            source="test",
        )
    )
    daily = _daily_for_bars(bars, _rising_closes(60))
    strat = PullbackLongV1(PullbackParams(sleeve="mid"), daily_bars=daily)
    settings = PaperSettings(
        equity_eur=40.0,
        per_trade_risk_frac=0.015,
        daily_kill_frac=0.05,
        one_position=True,
        time_stop_bars=8,
        leverage_default=1.0,
        leverage_hard_cap=1.0,
        fee_rate=0.0005,
        slippage_bps=5.0,
    )
    eng = PaperEngine(settings, strat, journal=NullJournal(), run_id="test-tp")
    summary = eng.run({"DOGE-USDT": bars}, {"DOGE-USDT": []}, universe=["DOGE-USDT"])
    assert summary.n_entries >= 1
    assert summary.n_trades >= 1
    reasons = [f.reason for f in summary.fills if f.kind == "exit"]
    assert reasons
    assert reasons[0] in ("take_profit", "time_stop", "stop", "regime_flat", "daily_kill")
