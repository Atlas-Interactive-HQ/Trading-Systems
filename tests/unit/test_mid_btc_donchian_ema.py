"""Unit tests: Mid BTC Donchian + EMA regime — new family vs pullback."""

from __future__ import annotations

import pytest

from atlas.paper.engine import PaperEngine, PaperSettings
from atlas.paper.eval import NullJournal
from atlas.paper.mid_btc_donchian_ema_eval import (
    LOW_FREQ_MEDIAN_CAP,
    MID_DD_CAP_EUR,
    MID_TIME_STOP_BARS,
    SPOT_MD,
    aggregate_set,
    score_mid,
)
from atlas.paper.types import Bar, Side
from atlas.strategy.breakout import donchian_prior
from atlas.strategy.mid_btc_donchian_ema import (
    FLAT,
    LONG,
    MidBtcDonchianEmaParams,
    MidBtcDonchianEmaV1,
    TradeWindowGate,
    regime_state,
)

DAY_MS = 86_400_000
EPOCH = 1_700_000_000_000
SYM = "BTC-USDT"


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


def _rising(n: int, start: float = 20_000.0, step: float = 400.0) -> list[float]:
    return [start + i * step for i in range(n)]


def _build_breakout_series() -> list[Bar]:
    """Steady uptrend then a clear close above prior 20-day high."""
    bars: list[Bar] = []
    px = 20_000.0
    for i in range(45):
        px = px * 1.012
        bars.append(_daily(SYM, i, px, high=px * 1.005, low=px * 0.995))
    # Quiet flat-ish bars so prior 20 high is set, then breakout close
    for j in range(5):
        i = 45 + j
        bars.append(_daily(SYM, i, px, high=px * 1.002, low=px * 0.998))
    prior = donchian_prior(bars, 20)
    assert prior is not None
    prior_high, _ = prior
    i = 50
    brk = float(prior_high) * 1.02
    bars.append(_daily(SYM, i, brk, high=brk * 1.01, low=brk * 0.99))
    return bars


def test_spot_md_is_btc_locked_params():
    assert SPOT_MD == "BTC-USDT"
    assert MID_DD_CAP_EUR == 16.0
    assert LOW_FREQ_MEDIAN_CAP == 15
    assert MID_TIME_STOP_BARS == 15


def test_regime_long_on_uptrend():
    closes = _rising(40)
    bars = [_daily(SYM, i, c) for i, c in enumerate(closes)]
    assert regime_state(bars) == LONG


def test_regime_flat_on_downtrend():
    closes = list(reversed(_rising(40)))
    bars = [_daily(SYM, i, c) for i, c in enumerate(closes)]
    assert regime_state(bars) == FLAT


def test_entry_on_donchian_breakout_with_regime():
    bars = _build_breakout_series()
    strat = MidBtcDonchianEmaV1()
    sig = strat.on_closed_bar(bars)
    assert sig is not None
    assert sig.side is Side.LONG
    assert sig.symbol == SYM
    assert sig.reason == "mid_btc_donchian_breakout"
    assert sig.extras["atr_stop"] is False
    assert sig.stop < bars[-1].close
    assert bars[-1].close > sig.extras["prior_20_high"]


def test_no_entry_without_breakout():
    closes = _rising(40, step=50.0)
    bars = [_daily(SYM, i, c) for i, c in enumerate(closes)]
    # Last close inside channel (not above prior high)
    strat = MidBtcDonchianEmaV1()
    # Force last bar to close below prior high
    ch = donchian_prior(bars, 20)
    assert ch is not None
    prior_high, prior_low = ch
    last = bars[-1]
    bars[-1] = Bar(
        symbol=SYM,
        ts_open_ms=last.ts_open_ms,
        ts_close_ms=last.ts_close_ms,
        open=prior_high * 0.99,
        high=prior_high * 0.995,
        low=prior_low * 1.01,
        close=prior_high * 0.99,
        volume=1e6,
        closed=True,
        source="test",
    )
    assert strat.on_closed_bar(bars) is None


def test_no_entry_when_regime_flat():
    closes = list(reversed(_rising(50, start=40_000.0, step=500.0)))
    bars = [_daily(SYM, i, c) for i, c in enumerate(closes)]
    assert regime_state(bars) == FLAT
    strat = MidBtcDonchianEmaV1()
    assert strat.on_closed_bar(bars) is None


def test_no_short_ever():
    bars = _build_breakout_series()
    strat = MidBtcDonchianEmaV1()
    sig = strat.on_closed_bar(bars)
    assert sig is None or sig.side is Side.LONG


def test_exit_hint_regime_flat():
    up = _rising(40, start=20_000.0, step=800.0)
    bars = [_daily(SYM, i, c) for i, c in enumerate(up)]
    assert regime_state(bars) == LONG
    px = up[-1]
    for j in range(25):
        px = px * 0.92
        bars.append(_daily(SYM, 40 + j, px))
    strat = MidBtcDonchianEmaV1()
    assert strat.exit_hint(Side.LONG, bars) == "regime_flat"


def test_exit_hint_donchian():
    bars = _build_breakout_series()
    strat = MidBtcDonchianEmaV1()
    assert regime_state(bars) == LONG
    ch = donchian_prior(bars, 10)
    assert ch is not None
    _, plow = ch
    # Single closed bar below prior 10-low (lookback excludes this bar).
    # Mild dip keeps EMA regime long so hint is donchian_exit, not regime_flat.
    deep = float(plow) * 0.999
    bars.append(
        _daily(SYM, len(bars), deep, high=max(deep, float(plow)) * 1.001, low=deep * 0.999)
    )
    hint = strat.exit_hint(Side.LONG, bars)
    assert hint == "donchian_exit"


def test_trade_window_gate_blocks_outside():
    bars = _build_breakout_series()
    inner = MidBtcDonchianEmaV1()
    gate = TradeWindowGate(inner, trade_start_ms=bars[0].ts_open_ms, trade_end_ms=bars[-1].ts_open_ms)
    assert gate.on_closed_bar(bars) is None
    gate2 = TradeWindowGate(
        inner,
        trade_start_ms=bars[0].ts_open_ms,
        trade_end_ms=bars[-1].ts_close_ms + 1,
    )
    assert gate2.on_closed_bar(bars) is not None


def test_score_mid_holdout_requires_positive_expectancy():
    full = {
        "ok": True,
        "expectancy_after_costs_eur": 0.50,
        "max_dd_eur": 1.0,
        "n_trades": 4,
    }
    hold_pos = {"ok": True, "expectancy_after_costs_eur": 0.10, "n_trades": 1, "max_dd_eur": 0.5}
    sc = score_mid(full, hold_pos, dd_cap_eur=16.0)
    assert sc["full_pass"] is True
    assert sc["holdout_ok_if_full_passed"] is True

    hold_neg = {"ok": True, "expectancy_after_costs_eur": -0.05, "n_trades": 1, "max_dd_eur": 0.5}
    sc2 = score_mid(full, hold_neg, dd_cap_eur=16.0)
    assert sc2["holdout_ok_if_full_passed"] is False

    hold_zero = {"ok": True, "expectancy_after_costs_eur": 0.0, "n_trades": 1, "max_dd_eur": 0.5}
    sc3 = score_mid(full, hold_zero, dd_cap_eur=16.0)
    assert sc3["holdout_ok_if_full_passed"] is False


def test_aggregate_median_is_pass_gate():
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
    assert ok["mid"]["low_freq_is_pass_gate"] is True

    too_many = aggregate_set([_wr("A1", 20), _wr("A2", 22), _wr("A3", 18)])
    assert too_many["verdict"] == "FAIL"
    assert too_many["mid"]["low_freq_ok"] is False


def test_engine_roundtrip_no_atr_tp():
    bars = _build_breakout_series()
    last = bars[-1]
    bars.append(
        Bar(
            symbol=SYM,
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
    for j in range(16):
        px = last.close * (1.002 + j * 0.001)
        bars.append(_daily(SYM, len(bars), px))

    settings = PaperSettings(
        equity_eur=40.0,
        per_trade_risk_frac=0.015,
        daily_kill_frac=0.05,
        one_position=True,
        time_stop_bars=15,
        leverage_default=1.0,
        leverage_hard_cap=1.0,
        fee_rate=0.0005,
        slippage_bps=5.0,
    )
    strat = MidBtcDonchianEmaV1()
    # Sanity: signal has no TP / no ATR flag
    sig = strat.on_closed_bar(bars[:51])
    assert sig is not None
    assert float(sig.extras.get("take_profit") or 0.0) == 0.0
    assert sig.extras.get("atr_stop") is False

    eng = PaperEngine(settings, strat, journal=NullJournal(), run_id="test-donch", data_dir="data")
    paper = eng.run({SYM: bars}, {SYM: []}, universe=[SYM])
    assert paper.n_entries >= 1
    assert paper.n_trades >= 0
