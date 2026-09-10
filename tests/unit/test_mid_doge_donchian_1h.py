"""Unit tests: Mid DOGE Donchian 20/10 on 1H — NO EMA; holdout-exp gate like #36."""

from __future__ import annotations

from atlas.paper.engine import PaperEngine, PaperSettings
from atlas.paper.eval import NullJournal
from atlas.paper.mid_doge_donchian_1h_eval import (
    BAR,
    LOW_FREQ_MEDIAN_CAP,
    MID_DD_CAP_EUR,
    MID_TIME_STOP_BARS,
    SPOT_MD,
    aggregate_set,
    score_mid,
)
from atlas.paper.types import Bar, Side
from atlas.strategy.breakout import donchian_prior
from atlas.strategy.mid_doge_donchian_1h import (
    ENTRY_LOOKBACK,
    EXIT_LOOKBACK,
    MidDogeDonchian1hParams,
    MidDogeDonchian1hV1,
    TradeWindowGate,
)

HOUR_MS = 3_600_000
EPOCH = 1_700_000_000_000
SYM = "DOGE-USDT"


def _h1(symbol: str, i: int, close: float, *, high: float | None = None, low: float | None = None) -> Bar:
    open_ms = EPOCH + i * HOUR_MS
    o = close
    h = high if high is not None else close * 1.01
    l = low if low is not None else close * 0.99
    return Bar(
        symbol=symbol,
        ts_open_ms=open_ms,
        ts_close_ms=open_ms + HOUR_MS,
        open=o,
        high=max(h, o, close),
        low=min(l, o, close),
        close=close,
        volume=1e6,
        closed=True,
        source="test",
    )


def _build_breakout_series() -> list[Bar]:
    """Steady uptrend then a clear close above prior 20-bar high."""
    bars: list[Bar] = []
    px = 0.10
    for i in range(45):
        px = px * 1.012
        bars.append(_h1(SYM, i, px, high=px * 1.005, low=px * 0.995))
    for j in range(5):
        i = 45 + j
        bars.append(_h1(SYM, i, px, high=px * 1.002, low=px * 0.998))
    prior = donchian_prior(bars, 20)
    assert prior is not None
    prior_high, _ = prior
    i = 50
    brk = float(prior_high) * 1.02
    bars.append(_h1(SYM, i, brk, high=brk * 1.01, low=brk * 0.99))
    return bars


def test_spot_md_bar_locked_params():
    assert SPOT_MD == "DOGE-USDT"
    assert BAR == "1H"
    assert ENTRY_LOOKBACK == 20
    assert EXIT_LOOKBACK == 10
    assert MID_DD_CAP_EUR == 16.0
    assert LOW_FREQ_MEDIAN_CAP == 15
    assert MID_TIME_STOP_BARS == 15


def test_no_ema_in_params_or_label():
    p = MidDogeDonchian1hParams()
    assert not hasattr(p, "ema_fast")
    strat = MidDogeDonchian1hV1()
    assert "ema" not in strat.label.lower()
    assert "1h" in strat.label.lower()


def test_entry_on_donchian_breakout_without_ema():
    bars = _build_breakout_series()
    strat = MidDogeDonchian1hV1()
    sig = strat.on_closed_bar(bars)
    assert sig is not None
    assert sig.side is Side.LONG
    assert sig.symbol == SYM
    assert sig.reason == "mid_doge_donchian_1h_breakout"
    assert sig.extras["atr_stop"] is False
    assert sig.extras["ema_regime"] is False
    assert sig.extras["bar"] == "1H"
    assert sig.stop < bars[-1].close
    assert bars[-1].close > sig.extras["prior_20_high"]


def test_no_entry_without_breakout():
    bars = _build_breakout_series()
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
    assert MidDogeDonchian1hV1().on_closed_bar(bars) is None


def test_no_short_ever():
    bars = _build_breakout_series()
    sig = MidDogeDonchian1hV1().on_closed_bar(bars)
    assert sig is None or sig.side is Side.LONG


def test_exit_hint_donchian_only_no_regime():
    bars = _build_breakout_series()
    strat = MidDogeDonchian1hV1()
    ch = donchian_prior(bars, 10)
    assert ch is not None
    _, plow = ch
    deep = float(plow) * 0.999
    bars.append(
        _h1(SYM, len(bars), deep, high=max(deep, float(plow)) * 1.001, low=deep * 0.999)
    )
    hint = strat.exit_hint(Side.LONG, bars)
    assert hint == "donchian_exit"
    assert strat.exit_hint(Side.LONG, _build_breakout_series()) is None


def test_trade_window_gate_blocks_outside():
    bars = _build_breakout_series()
    inner = MidDogeDonchian1hV1()
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


def test_engine_roundtrip_no_atr_tp_no_ema():
    bars = _build_breakout_series()
    last = bars[-1]
    bars.append(
        Bar(
            symbol=SYM,
            ts_open_ms=last.ts_close_ms,
            ts_close_ms=last.ts_close_ms + HOUR_MS,
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
        bars.append(_h1(SYM, len(bars), px))

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
    strat = MidDogeDonchian1hV1()
    sig = strat.on_closed_bar(bars[:51])
    assert sig is not None
    assert float(sig.extras.get("take_profit") or 0.0) == 0.0
    assert sig.extras.get("atr_stop") is False
    assert sig.extras.get("ema_regime") is False
    assert sig.extras.get("bar") == "1H"

    eng = PaperEngine(settings, strat, journal=NullJournal(), run_id="test-doge-donch-1h", data_dir="data")
    paper = eng.run({SYM: bars}, {SYM: []}, universe=[SYM])
    assert paper.n_entries >= 1
    assert paper.n_trades >= 0
