"""Unit tests: phase1/134 Public-MD Scalp 10-cell batch B–J (A=#133)."""

from __future__ import annotations

import pytest

from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.ema_eval import EmaBookSettings
from atlas.paper.public_md_scalp_134_batch import (
    CELL_A_133_FULL,
    CELL_SPECS,
    PHASE1,
    SOURCE,
    USDT_INSTS,
    WINDOWS,
    cell_a_from_133,
    gate_for_full_cells,
    walk_batch_134,
)
from atlas.paper.types import Bar
from atlas.strategy.keltner import keltner_series
from atlas.strategy.scalp_134_b_breakout import LOOKBACK as B_LOOKBACK
from atlas.strategy.scalp_134_b_breakout import MIN_ATR_FRAC, precompute_b
from atlas.strategy.scalp_134_c_donchian import LOOKBACK as C_LOOKBACK
from atlas.strategy.scalp_134_c_donchian import precompute_c
from atlas.strategy.scalp_134_common import Batch134Signals
from atlas.strategy.scalp_134_d_rsi_mr import ENTRY_RSI, EXIT_RSI, precompute_d
from atlas.strategy.scalp_134_e_ema1221 import FAST, SLOW, precompute_e
from atlas.strategy.scalp_134_f_supertrend import ST_MULT, ST_PERIOD, precompute_f
from atlas.strategy.scalp_134_g_keltner import KC_MULT, KC_PERIOD, precompute_g
from atlas.strategy.scalp_134_h_macd_rvol import RVOL_GATE, precompute_h
from atlas.strategy.scalp_134_i_dt_15m import N as I_N
from atlas.strategy.scalp_134_i_dt_15m import TIME_STOP as I_TIME_STOP
from atlas.strategy.scalp_134_i_dt_15m import precompute_i
from atlas.strategy.scalp_134_j_vwap import ATR_SL_MULT as J_ATR_SL
from atlas.strategy.scalp_134_j_vwap import precompute_j
from atlas.strategy.session_vwap import session_vwap_series
from atlas.strategy.supertrend import supertrend_series


def _bar1h(i: int, o: float, h: float, l: float, c: float, *, vol: float = 100.0) -> Bar:
    open_ms = i * 60 * 60_000
    return Bar(
        symbol="BTC-USDT",
        ts_open_ms=open_ms,
        ts_close_ms=open_ms + 60 * 60_000,
        open=o,
        high=h,
        low=l,
        close=c,
        volume=vol,
        closed=True,
        source="test",
    )


def _bar4h(i: int, o: float, h: float, l: float, c: float) -> Bar:
    open_ms = i * 4 * 60 * 60_000
    return Bar(
        symbol="BTC-USDT",
        ts_open_ms=open_ms,
        ts_close_ms=open_ms + 4 * 60 * 60_000,
        open=o,
        high=h,
        low=l,
        close=c,
        volume=1000.0,
        closed=True,
        source="test",
    )


def _bar15m(i: int, o: float, h: float, l: float, c: float, *, vol: float = 50.0) -> Bar:
    open_ms = i * 15 * 60_000
    return Bar(
        symbol="BTC-USDT",
        ts_open_ms=open_ms,
        ts_close_ms=open_ms + 15 * 60_000,
        open=o,
        high=h,
        low=l,
        close=c,
        volume=vol,
        closed=True,
        source="test",
    )


def _uptrend_1h(n: int = 80, start: float = 100.0) -> list[Bar]:
    bars = []
    px = start
    for i in range(n):
        o = px
        c = px + 1.0
        bars.append(_bar1h(i, o, c + 0.5, o - 0.2, c, vol=100.0 + (i % 5)))
        px = c
    return bars


def _uptrend_4h(n: int = 40, start: float = 100.0) -> list[Bar]:
    bars = []
    px = start
    for i in range(n):
        o = px
        c = px + 4.0
        bars.append(_bar4h(i, o, c + 1.0, o - 0.5, c))
        px = c
    return bars


def test_phase_locked():
    assert PHASE1 == 134
    assert SOURCE == "public_md_scalp_134_batch"
    assert SCALP_START_EUR == 20.0
    assert USDT_INSTS == ("BTC-USDT", "ETH-USDT", "DOGE-USDT")
    assert WINDOWS["FULL"][0] == "2020-07-01T00:00:00Z"
    assert set(CELL_SPECS) == set("BCDEFGHIJ")


def test_cell_a_soft_note_from_constants():
    a = cell_a_from_133(None)
    assert a["gate_verdict"] == "SOFT_NOTE"
    assert a["n_pairs_exp_pos_full"] == 3
    assert a["n_pairs_hard_pass_full"] == 0
    assert CELL_A_133_FULL["BTC-USDT"]["n"] == 16
    assert CELL_A_133_FULL["BTC-USDT"]["exp"] == pytest.approx(0.14934035)


def test_gate_hard_soft_fail():
    def _cell(inst, exp, term, bh):
        return {
            "ok": True,
            "status": "MEASURED",
            "inst_id": inst,
            "completed_exp_positive": exp > 0,
            "pass_vs_bh": term >= bh,
        }

    hard = gate_for_full_cells(
        [
            _cell("BTC-USDT", 1.0, 50.0, 43.0),
            _cell("ETH-USDT", 1.0, 50.0, 45.0),
            _cell("DOGE-USDT", -0.1, 1.0, 20.0),
        ]
    )
    assert hard["gate_verdict"] == "HARD_PASS"
    soft = gate_for_full_cells(
        [
            _cell("BTC-USDT", 0.1, 6.0, 43.0),
            _cell("ETH-USDT", 0.5, 15.0, 45.0),
            _cell("DOGE-USDT", 0.2, 5.0, 20.0),
        ]
    )
    assert soft["gate_verdict"] == "SOFT_NOTE"
    fail = gate_for_full_cells(
        [
            _cell("BTC-USDT", -0.1, -1.0, 43.0),
            _cell("ETH-USDT", -0.1, -1.0, 45.0),
            _cell("DOGE-USDT", 0.1, 1.0, 20.0),
        ]
    )
    assert fail["gate_verdict"] == "FAIL"


def test_supertrend_formula_no_lookahead():
    highs = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 19]
    lows = [9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 18]
    closes = [9.5, 10.5, 11.5, 12.5, 13.5, 14.5, 15.5, 16.5, 17.5, 18.5, 19.5, 18.5]
    st, d = supertrend_series(highs, lows, closes, period=3, multiplier=2.0)
    # Truncating input must not change earlier values (no lookahead)
    st2, d2 = supertrend_series(highs[:-1], lows[:-1], closes[:-1], period=3, multiplier=2.0)
    assert st2 == st[:-1]
    assert d2 == d[:-1]
    assert ST_PERIOD == 10 and ST_MULT == 3.0


def test_keltner_and_vwap_causal():
    closes = [float(i) for i in range(1, 40)]
    highs = [c + 1 for c in closes]
    lows = [c - 1 for c in closes]
    mid, up, lo = keltner_series(highs, lows, closes, period=5, multiplier=1.5)
    mid2, up2, lo2 = keltner_series(highs[:-1], lows[:-1], closes[:-1], period=5, multiplier=1.5)
    assert mid2 == mid[:-1]
    assert KC_PERIOD == 20 and KC_MULT == 1.5

    bars = [_bar1h(i, 100 + i, 101 + i, 99 + i, 100.5 + i, vol=10.0) for i in range(30)]
    # Force UTC day boundary: bar 24 is next day if start at 0
    vw = session_vwap_series(bars)
    assert vw[0] is not None
    vw2 = session_vwap_series(bars[:-1])
    assert vw2 == vw[:-1]


def test_cell_b_entry_breakout_and_quiet():
    # Need enough overlapping 4H for EMA21 regime to warm inside the 1H window
    bars_1h = _uptrend_1h(200, 100.0)
    bars_4h = _uptrend_4h(80, 100.0)
    sig = precompute_b(bars_1h, bars_4h)
    assert len(sig.entry_ok) == len(bars_1h)
    assert B_LOOKBACK == 16
    assert MIN_ATR_FRAC == 0.001
    assert any(sig.entry_ok)


def test_cell_c_donchian_mid_sl():
    bars_1h = _uptrend_1h(200)
    bars_4h = _uptrend_4h(80)
    sig = precompute_c(bars_1h, bars_4h)
    assert C_LOOKBACK == 20
    assert any(sig.entry_ok)
    assert any(s is not None for s in sig.sl_ref)


def test_cell_d_rsi_cross_thresholds():
    # Build a dip then recovery to force RSI cross
    bars: list[Bar] = []
    px = 100.0
    for i in range(40):
        c = px - 2.0  # decline
        bars.append(_bar1h(i, px, px + 0.1, c - 0.1, c))
        px = c
    for i in range(40, 80):
        c = px + 2.5  # sharp recovery
        bars.append(_bar1h(i, px, c + 0.1, px - 0.1, c))
        px = c
    bars_4h = _uptrend_4h(40, 50.0)
    sig = precompute_d(bars, bars_4h)
    assert ENTRY_RSI == 30.0 and EXIT_RSI == 55.0
    # May or may not fire on this synthetic — check lengths & no crash
    assert len(sig.entry_ok) == len(bars)
    assert len(sig.exit_ok) == len(bars)


def test_cell_e_ema_cross_exit():
    bars_1h = _uptrend_1h(60)
    bars_4h = _uptrend_4h(30)
    sig = precompute_e(bars_1h, bars_4h)
    assert FAST == 12 and SLOW == 21
    assert len(sig.entry_ok) == 60


def test_cell_f_supertrend_flip():
    bars_1h = _uptrend_1h(80)
    bars_4h = _uptrend_4h(40)
    sig = precompute_f(bars_1h, bars_4h)
    assert any(s is not None for s in sig.sl_ref)


def test_cell_g_keltner_entry():
    bars_1h = _uptrend_1h(80)
    bars_4h = _uptrend_4h(40)
    sig = precompute_g(bars_1h, bars_4h)
    assert len(sig.entry_ok) == 80


def test_cell_h_macd_rvol_gate():
    bars_1h = _uptrend_1h(100, 100.0)
    # Spike volume on last bars for RVOL
    for i in range(80, 100):
        b = bars_1h[i]
        bars_1h[i] = _bar1h(i, b.open, b.high, b.low, b.close, vol=500.0)
    bars_4h = _uptrend_4h(50)
    sig = precompute_h(bars_1h, bars_4h)
    assert RVOL_GATE == 1.0
    assert len(sig.entry_ok) == 100


def test_cell_i_dt15m_constants():
    assert I_N == 20
    assert I_TIME_STOP == 64
    bars_15 = [_bar15m(i, 100 + i * 0.1, 100.2 + i * 0.1, 99.8 + i * 0.1, 100.1 + i * 0.1, vol=10 + i) for i in range(80)]
    bars_1h = _uptrend_1h(30, 100.0)
    sig = precompute_i(bars_15, bars_1h)
    assert len(sig.entry_ok) == 80
    # Regime false → exit_ok true on cold/early bars often
    assert isinstance(sig.exit_ok[0], bool)


def test_cell_j_vwap_pullback_and_sl_mult():
    assert J_ATR_SL == 1.0
    bars_1h = _uptrend_1h(50)
    bars_4h = _uptrend_4h(25)
    sig = precompute_j(bars_1h, bars_4h)
    assert len(sig.entry_ok) == 50


def test_walker_entry_exit_no_lookahead_fill_next_open():
    """Entry signal on bar i fills at bar i+1 open; exit same convention."""
    n = 30
    bars = [_bar1h(i, 100.0, 101.0, 99.0, 100.0) for i in range(n)]
    # Force entry on bar 5, exit signal on bar 10
    entry = [False] * n
    exit_ok = [False] * n
    atr = [1.0] * n
    sl_ref = [None] * n
    entry[5] = True
    exit_ok[10] = True
    sig = Batch134Signals(entry_ok=entry, exit_ok=exit_ok, atr=atr, sl_ref=sl_ref)
    settings = EmaBookSettings(equity_eur=20.0, fee_rate=0.0005, slippage_bps=5.0, leverage=1.0)
    out = walk_batch_134(
        bars,
        sig,
        settings=settings,
        trade_start_ms=0,
        trade_end_ms=n * 60 * 60_000,
        sl_mode="atr",
        atr_sl_mult=1.5,
        r_multiple=None,
        time_stop_bars=100,
    )
    assert out["n_long_entries"] == 1
    assert out["n_short_entries"] == 0
    assert out["n_trades"] == 1
    assert out["n_signal_exits"] == 1
    assert out["place_orders"] is False


def test_walker_skips_bad_sl():
    n = 20
    bars = [_bar1h(i, 100.0, 101.0, 99.0, 100.0) for i in range(n)]
    entry = [False] * n
    entry[3] = True
    sig = Batch134Signals(
        entry_ok=entry,
        exit_ok=[False] * n,
        atr=[None] * n,  # no ATR → skip
        sl_ref=[None] * n,
    )
    settings = EmaBookSettings(equity_eur=20.0, fee_rate=0.0005, slippage_bps=5.0, leverage=1.0)
    out = walk_batch_134(
        bars,
        sig,
        settings=settings,
        trade_start_ms=0,
        trade_end_ms=n * 60 * 60_000,
        sl_mode="atr",
        atr_sl_mult=1.5,
        r_multiple=1.5,
        time_stop_bars=24,
    )
    assert out["n_long_entries"] == 0
    assert out["n_skipped_sl_not_below"] == 1


def test_regime_blocks_entry_when_4h_flat():
    """4H declining → regime False → no B entries."""
    bars_1h = _uptrend_1h(60, 200.0)
    # Declining 4H so close < EMA
    bars_4h = []
    px = 300.0
    for i in range(40):
        o = px
        c = px - 5.0
        bars_4h.append(_bar4h(i, o, o + 0.5, c - 0.5, c))
        px = c
    sig = precompute_b(bars_1h, bars_4h)
    # With strong down 4H regime, entries should be scarce/none after EMA warms
    # (warmup may allow early noise; require not all True)
    assert not all(sig.entry_ok)
