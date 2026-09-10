"""Unit tests: Mid BTC daily EMA pullback — reuse MidDailyPullbackV1 + stricter score gates."""

from __future__ import annotations

import pytest

from atlas.paper.engine import PaperEngine, PaperSettings
from atlas.paper.eval import NullJournal
from atlas.paper.mid_btc_daily_pullback_eval import (
    LOW_FREQ_MEDIAN_CAP,
    MID_DD_CAP_EUR,
    SPOT_MD,
    aggregate_set,
    score_mid,
)
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


def _build_reclaim_series() -> list[Bar]:
    """Uptrend then dip then reclaim close — BTC-scale prices."""
    bars: list[Bar] = []
    px = 20_000.0
    for i in range(50):
        px = px * 1.015
        bars.append(_daily(SYM, i, px))
    for j in range(2):
        i = 50 + j
        px = px * 0.97
        bars.append(_daily(SYM, i, px, low=px * 0.95, high=px * 1.01))
    i = 52
    px = px * 1.04
    bars.append(_daily(SYM, i, px, high=px * 1.02, low=px * 0.96))
    return bars


def test_spot_md_is_btc():
    assert SPOT_MD == "BTC-USDT"
    assert MID_DD_CAP_EUR == 16.0
    assert LOW_FREQ_MEDIAN_CAP == 15


def test_regime_long_on_uptrend():
    closes = _rising(40)
    bars = [_daily(SYM, i, c) for i, c in enumerate(closes)]
    assert regime_state(bars) == LONG


def test_regime_flat_on_downtrend():
    closes = list(reversed(_rising(40)))
    bars = [_daily(SYM, i, c) for i, c in enumerate(closes)]
    assert regime_state(bars) == FLAT


def test_entry_on_pullback_reclaim():
    bars = _build_reclaim_series()
    strat = MidDailyPullbackV1()
    sig = strat.on_closed_bar(bars)
    assert sig is not None
    assert sig.side is Side.LONG
    assert sig.symbol == SYM
    assert sig.extras["take_profit"] > bars[-1].close
    assert sig.stop < bars[-1].close
    r = (sig.extras["take_profit"] - bars[-1].close) / (bars[-1].close - sig.stop)
    assert r == pytest.approx(2.0, rel=1e-6)


def test_no_short_ever():
    bars = _build_reclaim_series()
    strat = MidDailyPullbackV1()
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
    strat = MidDailyPullbackV1()
    assert strat.exit_hint(Side.LONG, bars) == "regime_flat"


def test_trade_window_gate_blocks_outside():
    bars = _build_reclaim_series()
    inner = MidDailyPullbackV1()
    gate = TradeWindowGate(inner, trade_start_ms=bars[0].ts_open_ms, trade_end_ms=bars[-1].ts_open_ms)
    assert gate.on_closed_bar(bars) is None
    gate2 = TradeWindowGate(
        inner,
        trade_start_ms=bars[0].ts_open_ms,
        trade_end_ms=bars[-1].ts_close_ms + 1,
    )
    assert gate2.on_closed_bar(bars) is not None


def test_score_mid_holdout_requires_positive_expectancy():
    """Stricter than DOGE: holdout exp must be > 0, not merely ≥ full."""
    full = {
        "ok": True,
        "expectancy_after_costs_eur": 0.50,
        "max_dd_eur": 1.0,
        "n_trades": 4,
    }
    # Positive but worse than full — still PASS under BTC rule
    hold_pos = {"ok": True, "expectancy_after_costs_eur": 0.10, "n_trades": 1, "max_dd_eur": 0.5}
    sc = score_mid(full, hold_pos, dd_cap_eur=16.0)
    assert sc["full_pass"] is True
    assert sc["holdout_ok_if_full_passed"] is True

    # Negative holdout — FAIL under BTC rule (would also fail DOGE)
    hold_neg = {"ok": True, "expectancy_after_costs_eur": -0.05, "n_trades": 1, "max_dd_eur": 0.5}
    sc2 = score_mid(full, hold_neg, dd_cap_eur=16.0)
    assert sc2["holdout_ok_if_full_passed"] is False

    # Zero holdout — FAIL (must be > 0)
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

    ok = aggregate_set([_wr("A1", 4), _wr("A2", 5), _wr("A3", 3)])
    assert ok["verdict"] == "PASS"
    assert ok["mid"]["low_freq_is_pass_gate"] is True

    too_many = aggregate_set([_wr("A1", 20), _wr("A2", 22), _wr("A3", 18)])
    assert too_many["verdict"] == "FAIL"
    assert too_many["mid"]["low_freq_ok"] is False


def test_engine_roundtrip_tp_or_exit():
    bars = _build_reclaim_series()
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
    e = bars[-1]
    bars.append(
        Bar(
            symbol=SYM,
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
    eng = PaperEngine(settings, strat, journal=NullJournal(), run_id="test-mid-btc-daily-tp")
    summary = eng.run({SYM: bars}, {SYM: []}, universe=[SYM])
    assert summary.n_entries >= 1
    assert summary.n_trades >= 1
    reasons = [f.reason for f in summary.fills if f.kind == "exit"]
    assert reasons
    assert reasons[0] in ("take_profit", "time_stop", "stop", "regime_flat", "daily_kill")
