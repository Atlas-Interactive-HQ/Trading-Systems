"""Unit tests: phase1/136 L1 Keltner + L2 Donchian 1D EMA21 hold. No S4/D/J."""

from __future__ import annotations

import pytest

from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.ema_eval import EmaBookSettings
from atlas.paper.public_md_scalp_136 import (
    BH_FULL_CITE,
    CELL_SPECS,
    EMA_1D,
    EMA_4H,
    OFFICIAL_CELLS,
    PARENT_FULL,
    PHASE1,
    SOURCE,
    TIME_STOP,
    USDT_INSTS,
    WINDOWS,
    assert_sid_allowed,
    candidate_id_for,
    gate_for_full_cells,
    resample_1d_from_4h,
    resolve_fixed_sl,
    walk_scalp_136,
)
from atlas.paper.types import Bar
from atlas.strategy.scalp_136_common import (
    FORBIDDEN_CELLS,
    NO_4H_EMA_FLIP_EXIT,
    NO_ATR_TRAIL,
    NO_R_TP,
    Scalp136Signals,
    regime_flip_series_1d_ema21,
)
from atlas.strategy.scalp_136_l1_keltner import KC_MULT, KC_PERIOD, precompute_l1_keltner
from atlas.strategy.scalp_136_l2_donchian import LOOKBACK, precompute_l2_donchian


H1 = 60 * 60_000
H4 = 4 * H1
D1 = 24 * H1


def _bar1h(i: int, o: float, h: float, l: float, c: float, *, vol: float = 100.0) -> Bar:
    open_ms = i * H1
    return Bar(
        symbol="BTC-USDT",
        ts_open_ms=open_ms,
        ts_close_ms=open_ms + H1,
        open=o,
        high=h,
        low=l,
        close=c,
        volume=vol,
        closed=True,
        source="test",
    )


def _bar4h(i: int, o: float, h: float, l: float, c: float) -> Bar:
    open_ms = i * H4
    return Bar(
        symbol="BTC-USDT",
        ts_open_ms=open_ms,
        ts_close_ms=open_ms + H4,
        open=o,
        high=h,
        low=l,
        close=c,
        volume=1000.0,
        closed=True,
        source="test",
    )


def _bar1d(i: int, o: float, h: float, l: float, c: float) -> Bar:
    open_ms = i * D1
    return Bar(
        symbol="BTC-USDT",
        ts_open_ms=open_ms,
        ts_close_ms=open_ms + D1,
        open=o,
        high=h,
        low=l,
        close=c,
        volume=10_000.0,
        closed=True,
        source="test",
    )


def _settings() -> EmaBookSettings:
    return EmaBookSettings(
        equity_eur=20.0, fee_rate=0.0005, slippage_bps=5.0, leverage=1.0
    )


def _sig(n: int, **overrides: object) -> Scalp136Signals:
    base = dict(
        entry_ok=[False] * n,
        regime_flip=[False] * n,
        regime_flip_4h=[False] * n,
        sl_ref=[95.0] * n,
        atr=[1.0] * n,
    )
    base.update(overrides)
    return Scalp136Signals(**base)  # type: ignore[arg-type]


def test_phase_and_official_cells():
    assert PHASE1 == 136
    assert SOURCE == "public_md_scalp_136"
    assert OFFICIAL_CELLS == ("L1", "L2")
    assert set(CELL_SPECS) == set(OFFICIAL_CELLS)
    assert CELL_SPECS["L1"].family == "l1_keltner"
    assert CELL_SPECS["L2"].family == "l2_donchian"
    assert CELL_SPECS["L1"].parent_sid == "S2"
    assert CELL_SPECS["L1"].parent_letter == "G"
    assert CELL_SPECS["L2"].parent_sid == "S3"
    assert CELL_SPECS["L2"].parent_letter == "C"
    assert SCALP_START_EUR == 20.0
    assert TIME_STOP == 504
    assert EMA_4H == 21
    assert EMA_1D == 21
    assert NO_R_TP is True
    assert NO_4H_EMA_FLIP_EXIT is True
    assert NO_ATR_TRAIL is True
    assert KC_PERIOD == 20 and KC_MULT == 1.5
    assert LOOKBACK == 20


def test_reject_s4_and_dj():
    for bad in ("S4", "D", "J", "A", "S1", "S2", "S3"):
        with pytest.raises(ValueError):
            assert_sid_allowed(bad)
    assert "S4" in FORBIDDEN_CELLS
    assert "D" in FORBIDDEN_CELLS
    assert "J" in FORBIDDEN_CELLS


def test_candidate_ids():
    btc = candidate_id_for("L1", "BTC-USDT")
    eth = candidate_id_for("L2", "ETH-USDT")
    doge = candidate_id_for("L1", "DOGE-USDT")
    assert btc == "public_md_v1_136_l1_keltner_1d_ema21_flip_ts504_btc_usdt_eur20"
    assert eth == "public_md_v1_136_l2_donchian_1d_ema21_flip_ts504_eth_usdt_eur20"
    assert doge.endswith("_doge_usdt_eur20")
    assert "1.5r" not in btc.lower()
    assert "atrtrail" not in btc
    assert "s4" not in btc


def test_parent_baselines_honesty():
    assert PARENT_FULL["L1"]["BTC-USDT"]["n"] == 42
    assert PARENT_FULL["L1"]["BTC-USDT"]["exp"] == pytest.approx(0.15325586)
    assert PARENT_FULL["L1"]["ETH-USDT"]["terminal"] == pytest.approx(37.52870935)
    assert PARENT_FULL["L1"]["DOGE-USDT"]["exp"] == pytest.approx(0.3719052)
    assert PARENT_FULL["L2"]["BTC-USDT"]["n"] == 47
    assert PARENT_FULL["L2"]["BTC-USDT"]["exp"] == pytest.approx(0.23176435)
    assert PARENT_FULL["L2"]["ETH-USDT"]["terminal"] == pytest.approx(29.23997864)
    assert PARENT_FULL["L2"]["DOGE-USDT"]["n"] == 34
    assert BH_FULL_CITE["BTC-USDT"] == pytest.approx(43.17666206)
    assert BH_FULL_CITE["ETH-USDT"] == pytest.approx(45.16769469)
    assert BH_FULL_CITE["DOGE-USDT"] == pytest.approx(20.2301366)
    assert USDT_INSTS == ("BTC-USDT", "ETH-USDT", "DOGE-USDT")
    assert WINDOWS["FULL"][0] == "2020-07-01T00:00:00Z"


def test_reject_1_5r_does_not_flatten():
    """Even if price runs 10R, walker must not take TP (no 1.5R)."""
    n = 30
    bars = []
    px = 100.0
    for i in range(n):
        o = px
        c = px + 5.0
        bars.append(_bar1h(i, o, c + 1, o - 0.1, c))
        px = c
    entry_ok = [False] * n
    entry_ok[1] = True
    sl_ref = [99.0] * n
    sig = _sig(n, entry_ok=entry_ok, sl_ref=sl_ref)
    out = walk_scalp_136(
        bars,
        sig,
        settings=_settings(),
        trade_start_ms=0,
        trade_end_ms=10**12,
        time_stop_bars=504,
    )
    assert out["n_tp_exits"] == 0
    assert out["n_trail_exits"] == 0
    assert out["r_multiple"] is None
    assert out["n_long_entries"] >= 1


def test_ts504_time_stop():
    n = 520
    bars = [_bar1h(i, 100, 101, 99, 100.5) for i in range(n)]
    entry_ok = [False] * n
    entry_ok[1] = True
    sig = _sig(n, entry_ok=entry_ok, sl_ref=[90.0] * n)
    out = walk_scalp_136(
        bars,
        sig,
        settings=_settings(),
        trade_start_ms=0,
        trade_end_ms=10**12,
        time_stop_bars=504,
    )
    assert out["n_time_stop_exits"] >= 1
    assert out["time_stop_bars"] == 504
    assert out["n_tp_exits"] == 0
    # Must not fire at 168 (the #135 stop)
    out168 = walk_scalp_136(
        bars[:200],
        _sig(200, entry_ok=[False, True] + [False] * 198, sl_ref=[90.0] * 200),
        settings=_settings(),
        trade_start_ms=0,
        trade_end_ms=10**12,
        time_stop_bars=504,
    )
    assert out168["n_time_stop_exits"] == 0
    assert out168["n_long_entries"] == 1


def test_1d_flip_exits_next_1h_open():
    n = 20
    bars = [_bar1h(i, 100, 101, 99, 100.5) for i in range(n)]
    entry_ok = [False] * n
    entry_ok[1] = True
    flip = [False] * n
    flip[6] = True
    sig = _sig(n, entry_ok=entry_ok, regime_flip=flip, sl_ref=[90.0] * n)
    out = walk_scalp_136(
        bars,
        sig,
        settings=_settings(),
        trade_start_ms=0,
        trade_end_ms=10**12,
        time_stop_bars=504,
    )
    assert out["n_1d_flip_exits"] >= 1
    assert out["n_regime_flip_exits"] >= 1
    assert out["exit_mix"]["1d_flip"] >= 1
    assert out["n_tp_exits"] == 0


def test_4h_flip_does_not_exit():
    """4H close < EMA21 must NOT flatten; only 1D flip / SL / ts504."""
    n = 20
    bars = [_bar1h(i, 100, 101, 99, 100.5) for i in range(n)]
    entry_ok = [False] * n
    entry_ok[1] = True
    flip_4h = [False] * n
    flip_4h[5] = True
    flip_4h[6] = True
    flip_4h[7] = True
    sig = _sig(
        n,
        entry_ok=entry_ok,
        regime_flip=[False] * n,
        regime_flip_4h=flip_4h,
        sl_ref=[90.0] * n,
    )
    out = walk_scalp_136(
        bars,
        sig,
        settings=_settings(),
        trade_start_ms=0,
        trade_end_ms=10**12,
        time_stop_bars=504,
    )
    assert out["n_regime_flip_exits"] == 0
    assert out["n_1d_flip_exits"] == 0
    assert out["n_4h_flip_ignored"] >= 1
    assert out["n_long_entries"] == 1
    assert out["n_tp_exits"] == 0


def test_1d_flip_no_lookahead():
    """1H bars closing before the 1D close must not see that 1D flip."""
    # 25 closed 1D bars. First 24 close well above a rising path so EMA is
    # defined; the last 1D (day 24) closes far below EMA → flip.
    bars_1d: list[Bar] = []
    px = 100.0
    for i in range(24):
        o = px
        c = px + 1.0
        bars_1d.append(_bar1d(i, o, c + 1, o - 0.5, c))
        px = c
    # Day 24: crash below EMA
    bars_1d.append(_bar1d(24, px, px + 0.5, 50.0, 50.0))

    # 1H bars covering day 24 (index 24*24 = 576) through the 1D close at 25*D1
    # and a few hours after.
    n_1h = 25 * 24 + 4
    bars_1h = [_bar1h(i, 100, 101, 99, 100.5) for i in range(n_1h)]

    flip = regime_flip_series_1d_ema21(bars_1h, bars_1d, ema_period=21)
    day24_close_ms = 25 * D1  # 1D bar 24 closes here
    # Last 1H of day 24 opens at 24*24+23 = 599, closes at 25*D1
    last_hour_of_day24 = 24 * 24 + 23
    assert bars_1h[last_hour_of_day24].ts_close_ms == day24_close_ms
    # Hours before that 1D close must not see the crash
    assert flip[last_hour_of_day24 - 1] is False
    # The 1H that closes at the 1D close may see it (no lookahead into future)
    assert flip[last_hour_of_day24] is True
    # Subsequent 1H bars keep the last closed 1D
    assert flip[last_hour_of_day24 + 1] is True
    # Early 1H (day 0) has no EMA yet or is not flipped
    assert flip[0] is False


def test_resample_1d_from_6_closed_4h():
    """6 consecutive UTC-aligned closed 4H → one 1D. Incomplete dropped."""
    bars_4h = []
    # Day 0: complete 6
    for i in range(6):
        bars_4h.append(_bar4h(i, 100 + i, 110 + i, 90 + i, 105 + i))
    # Day 1: only 3 (incomplete — drop)
    for i in range(6, 9):
        bars_4h.append(_bar4h(i, 110, 120, 100, 115))
    out = resample_1d_from_4h(bars_4h)
    assert len(out) == 1
    d0 = out[0]
    assert d0.ts_open_ms == 0
    assert d0.ts_close_ms == D1
    assert d0.open == pytest.approx(100.0)
    assert d0.close == pytest.approx(105 + 5)
    assert d0.high == pytest.approx(110 + 5)
    assert d0.low == pytest.approx(90.0)
    assert d0.source == "resample_4h_6bars"
    assert d0.closed is True


def test_fixed_sl_helper():
    assert resolve_fixed_sl(entry_px=100.0, sl_ref=95.0) == 95.0
    assert resolve_fixed_sl(entry_px=100.0, sl_ref=100.0) is None
    assert resolve_fixed_sl(entry_px=100.0, sl_ref=101.0) is None
    assert resolve_fixed_sl(entry_px=0.0, sl_ref=95.0) is None


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


def test_precompute_lengths_match_and_4h_flip_not_used_as_exit():
    bars_1h = [
        _bar1h(i, 100 + i * 0.1, 101 + i * 0.1, 99 + i * 0.1, 100.5 + i * 0.1)
        for i in range(80)
    ]
    bars_4h = [_bar4h(i, 100 + i, 105 + i, 99 + i, 104 + i) for i in range(40)]
    bars_1d = [_bar1d(i, 100 + i, 110 + i, 90 + i, 108 + i) for i in range(30)]
    for fn in (precompute_l1_keltner, precompute_l2_donchian):
        sig = fn(bars_1h, bars_4h, bars_1d)
        assert len(sig.entry_ok) == len(bars_1h)
        assert len(sig.regime_flip) == len(bars_1h)
        assert len(sig.regime_flip_4h) == len(bars_1h)
        assert len(sig.sl_ref) == len(bars_1h)
        # Walker must use regime_flip (1D) not regime_flip_4h
        n = len(bars_1h)
        out = walk_scalp_136(
            bars_1h,
            sig,
            settings=_settings(),
            trade_start_ms=0,
            trade_end_ms=10**12,
            time_stop_bars=504,
        )
        assert out["n_tp_exits"] == 0
        assert out["n_trail_exits"] == 0
        # If 4H would have flipped but 1D did not, walker stays
        if any(sig.regime_flip_4h) and not any(sig.regime_flip):
            assert out["n_regime_flip_exits"] == 0
        del n
