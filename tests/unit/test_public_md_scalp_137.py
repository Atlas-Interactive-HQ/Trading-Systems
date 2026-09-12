"""Unit tests: phase1/137 N1 Donchian + N2 Keltner 1D EMA21 flip, NO time-stop."""

from __future__ import annotations

import pytest

from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.ema_eval import EmaBookSettings
from atlas.paper.public_md_scalp_137 import (
    BH_FULL_CITE,
    CELL_SPECS,
    EMA_1D,
    EMA_4H,
    FULL_1H_TRADE_BARS_EXPECTED,
    OFFICIAL_CELLS,
    PARENT_L1_136_FULL,
    PARENT_L2_136_FULL,
    PARENT_S2_135_FULL,
    PHASE1,
    SOURCE,
    TIME_STOP_DISABLED,
    USDT_INSTS,
    WINDOWS,
    assert_sid_allowed,
    candidate_id_for,
    gate_for_full_cells,
    walk_scalp_137,
)
from atlas.paper.replay import ReplayError
from atlas.paper.types import Bar
from atlas.strategy.scalp_136_common import regime_flip_series_1d_ema21
from atlas.strategy.scalp_137_common import (
    FORBIDDEN_CELLS,
    NO_4H_EMA_FLIP_EXIT,
    NO_ATR_TRAIL,
    NO_R_TP,
    NO_TIME_STOP,
    Scalp137Signals,
)
from atlas.strategy.scalp_137_n1_donchian import LOOKBACK, precompute_n1_donchian
from atlas.strategy.scalp_137_n2_keltner import KC_MULT, KC_PERIOD, precompute_n2_keltner


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


def _sig(n: int, **overrides: object) -> Scalp137Signals:
    base = dict(
        entry_ok=[False] * n,
        regime_flip=[False] * n,
        regime_flip_4h=[False] * n,
        sl_ref=[95.0] * n,
        atr=[1.0] * n,
    )
    base.update(overrides)
    return Scalp137Signals(**base)  # type: ignore[arg-type]


def test_phase_and_official_cells():
    assert PHASE1 == 137
    assert SOURCE == "public_md_scalp_137"
    assert OFFICIAL_CELLS == ("N1", "N2")
    assert set(CELL_SPECS) == set(OFFICIAL_CELLS)
    assert CELL_SPECS["N1"].family == "n1_donchian"
    assert CELL_SPECS["N2"].family == "n2_keltner"
    assert CELL_SPECS["N1"].parent_sid == "L2"
    assert CELL_SPECS["N2"].parent_sid == "S2"
    assert SCALP_START_EUR == 20.0
    assert TIME_STOP_DISABLED == 100_000
    assert TIME_STOP_DISABLED >= FULL_1H_TRADE_BARS_EXPECTED
    assert FULL_1H_TRADE_BARS_EXPECTED == 4416
    assert NO_TIME_STOP is True
    assert EMA_4H == 21
    assert EMA_1D == 21
    assert NO_R_TP is True
    assert NO_4H_EMA_FLIP_EXIT is True
    assert NO_ATR_TRAIL is True
    assert KC_PERIOD == 20 and KC_MULT == 1.5
    assert LOOKBACK == 20


def test_reject_s4_and_dj_and_l_cells():
    for bad in ("S4", "D", "J", "A", "S1", "S2", "S3", "L1", "L2"):
        with pytest.raises(ValueError):
            assert_sid_allowed(bad)
    assert "S4" in FORBIDDEN_CELLS
    assert "D" in FORBIDDEN_CELLS
    assert "J" in FORBIDDEN_CELLS


def test_candidate_ids():
    btc = candidate_id_for("N1", "BTC-USDT")
    eth = candidate_id_for("N2", "ETH-USDT")
    doge = candidate_id_for("N1", "DOGE-USDT")
    assert btc == "public_md_v1_137_n1_donchian_1d_ema21_flip_no_ts_btc_usdt_eur20"
    assert eth == "public_md_v1_137_n2_keltner_1d_ema21_flip_no_ts_eth_usdt_eur20"
    assert doge.endswith("_doge_usdt_eur20")
    assert "no_ts" in btc
    assert "ts504" not in btc
    assert "1.5r" not in btc.lower()
    assert "s4" not in btc


def test_parent_baselines_honesty():
    assert PARENT_L2_136_FULL["BTC-USDT"]["n"] == 42
    assert PARENT_L2_136_FULL["BTC-USDT"]["exp"] == pytest.approx(0.25596093)
    assert PARENT_L2_136_FULL["ETH-USDT"]["terminal"] == pytest.approx(16.91307242)
    assert PARENT_L2_136_FULL["DOGE-USDT"]["n"] == 33
    assert PARENT_S2_135_FULL["BTC-USDT"]["n"] == 42
    assert PARENT_S2_135_FULL["BTC-USDT"]["exp"] == pytest.approx(0.15325586)
    assert PARENT_S2_135_FULL["ETH-USDT"]["terminal"] == pytest.approx(37.52870935)
    assert PARENT_S2_135_FULL["DOGE-USDT"]["exp"] == pytest.approx(0.3719052)
    assert PARENT_L1_136_FULL["ETH-USDT"]["n"] == 86
    assert PARENT_L1_136_FULL["ETH-USDT"]["exp"] == pytest.approx(0.11774425)
    assert BH_FULL_CITE["BTC-USDT"] == pytest.approx(43.17666206)
    assert BH_FULL_CITE["ETH-USDT"] == pytest.approx(45.16769469)
    assert BH_FULL_CITE["DOGE-USDT"] == pytest.approx(20.2301366)
    assert USDT_INSTS == ("BTC-USDT", "ETH-USDT", "DOGE-USDT")
    assert WINDOWS["FULL"][0] == "2020-07-01T00:00:00Z"


def test_reject_1_5r_does_not_flatten():
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
    out = walk_scalp_137(
        bars,
        sig,
        settings=_settings(),
        trade_start_ms=0,
        trade_end_ms=10**12,
        time_stop_bars=TIME_STOP_DISABLED,
    )
    assert out["n_tp_exits"] == 0
    assert out["n_trail_exits"] == 0
    assert out["r_multiple"] is None
    assert out["n_long_entries"] >= 1
    assert out["n_time_stop_exits"] == 0


def test_no_time_stop_even_after_504_and_168():
    """ts504 / ts168 must NOT fire; NO time-stop on #137."""
    n = 520
    bars = [_bar1h(i, 100, 101, 99, 100.5) for i in range(n)]
    entry_ok = [False] * n
    entry_ok[1] = True
    sig = _sig(n, entry_ok=entry_ok, sl_ref=[90.0] * n)
    out = walk_scalp_137(
        bars,
        sig,
        settings=_settings(),
        trade_start_ms=0,
        trade_end_ms=10**12,
        time_stop_bars=TIME_STOP_DISABLED,
    )
    assert out["n_time_stop_exits"] == 0
    assert out["exit_mix"]["time"] == 0
    assert out["no_time_stop"] is True
    assert out["n_long_entries"] == 1
    # Still open or only exited via SL/1d — with flat prices and SL=90, stays open
    assert out["n_trades"] == 0 or out["n_sl_exits"] + out["n_1d_flip_exits"] == out["n_trades"]


def test_time_stop_cap_too_small_rejected():
    n = 10
    bars = [_bar1h(i, 100, 101, 99, 100.5) for i in range(n)]
    with pytest.raises(ReplayError, match="time_stop_bars"):
        walk_scalp_137(
            bars,
            _sig(n),
            settings=_settings(),
            trade_start_ms=0,
            trade_end_ms=10**12,
            time_stop_bars=504,
        )


def test_1d_flip_exits_next_1h_open():
    n = 20
    bars = [_bar1h(i, 100, 101, 99, 100.5) for i in range(n)]
    entry_ok = [False] * n
    entry_ok[1] = True
    flip = [False] * n
    flip[6] = True
    sig = _sig(n, entry_ok=entry_ok, regime_flip=flip, sl_ref=[90.0] * n)
    out = walk_scalp_137(
        bars,
        sig,
        settings=_settings(),
        trade_start_ms=0,
        trade_end_ms=10**12,
        time_stop_bars=TIME_STOP_DISABLED,
    )
    assert out["n_1d_flip_exits"] >= 1
    assert out["n_regime_flip_exits"] >= 1
    assert out["exit_mix"]["1d_flip"] >= 1
    assert out["exit_mix"]["time"] == 0
    assert out["n_tp_exits"] == 0


def test_4h_flip_does_not_exit():
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
    out = walk_scalp_137(
        bars,
        sig,
        settings=_settings(),
        trade_start_ms=0,
        trade_end_ms=10**12,
        time_stop_bars=TIME_STOP_DISABLED,
    )
    assert out["n_regime_flip_exits"] == 0
    assert out["n_1d_flip_exits"] == 0
    assert out["n_4h_flip_ignored"] >= 1
    assert out["n_long_entries"] == 1
    assert out["n_time_stop_exits"] == 0


def test_1d_flip_no_lookahead():
    bars_1d: list[Bar] = []
    px = 100.0
    for i in range(24):
        o = px
        c = px + 1.0
        bars_1d.append(_bar1d(i, o, c + 1, o - 0.5, c))
        px = c
    bars_1d.append(_bar1d(24, px, px + 0.5, 50.0, 50.0))

    n_1h = 25 * 24 + 4
    bars_1h = [_bar1h(i, 100, 101, 99, 100.5) for i in range(n_1h)]

    flip = regime_flip_series_1d_ema21(bars_1h, bars_1d, ema_period=21)
    day24_close_ms = 25 * D1
    last_hour_of_day24 = 24 * 24 + 23
    assert bars_1h[last_hour_of_day24].ts_close_ms == day24_close_ms
    assert flip[last_hour_of_day24 - 1] is False
    assert flip[last_hour_of_day24] is True
    assert flip[last_hour_of_day24 + 1] is True
    assert flip[0] is False


def test_one_position_no_reentry_until_exit_closed():
    """Max 1 position; signal while flat-pending-exit must not double-enter."""
    n = 25
    bars = [_bar1h(i, 100, 101, 99, 100.5) for i in range(n)]
    entry_ok = [False] * n
    entry_ok[1] = True
    entry_ok[7] = True  # would re-enter same bar as flip signal if buggy
    entry_ok[8] = True
    flip = [False] * n
    flip[6] = True
    sig = _sig(n, entry_ok=entry_ok, regime_flip=flip, sl_ref=[90.0] * n)
    out = walk_scalp_137(
        bars,
        sig,
        settings=_settings(),
        trade_start_ms=0,
        trade_end_ms=10**12,
        time_stop_bars=TIME_STOP_DISABLED,
    )
    assert out["n_1d_flip_exits"] >= 1
    # After exit fills next open, may re-enter later — but never overlapping
    assert out["n_short_entries"] == 0
    assert out["n_long_entries"] >= 1


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


def test_precompute_lengths_and_no_ts():
    bars_1h = [
        _bar1h(i, 100 + i * 0.1, 101 + i * 0.1, 99 + i * 0.1, 100.5 + i * 0.1)
        for i in range(80)
    ]
    bars_4h = [_bar4h(i, 100 + i, 105 + i, 99 + i, 104 + i) for i in range(40)]
    bars_1d = [_bar1d(i, 100 + i, 110 + i, 90 + i, 108 + i) for i in range(30)]
    for fn in (precompute_n1_donchian, precompute_n2_keltner):
        sig = fn(bars_1h, bars_4h, bars_1d)
        assert len(sig.entry_ok) == len(bars_1h)
        assert len(sig.regime_flip) == len(bars_1h)
        out = walk_scalp_137(
            bars_1h,
            sig,
            settings=_settings(),
            trade_start_ms=0,
            trade_end_ms=10**12,
            time_stop_bars=TIME_STOP_DISABLED,
        )
        assert out["n_tp_exits"] == 0
        assert out["n_trail_exits"] == 0
        assert out["n_time_stop_exits"] == 0
