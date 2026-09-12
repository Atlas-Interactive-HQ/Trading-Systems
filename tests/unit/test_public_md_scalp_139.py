"""Unit tests: phase1/139 D1 no-SL / D2 always-in / D3 dual-EMA."""

from __future__ import annotations

import pytest

from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.ema_eval import EmaBookSettings
from atlas.paper.public_md_scalp_139 import (
    BH_FULL_CITE,
    CELL_SPECS,
    EMA_1D,
    EMA_1D_SLOW,
    FULL_1H_TRADE_BARS_EXPECTED,
    OFFICIAL_CELLS,
    PARENT_C2_138_FULL,
    PARENT_S2_135_FULL,
    PHASE1,
    SOURCE,
    TIME_STOP_DISABLED,
    USDT_INSTS,
    WINDOWS,
    assert_sid_allowed,
    candidate_id_for,
    gate_for_full_cells,
    walk_scalp_139_alwaysin,
    walk_scalp_139_long_nosl,
)
from atlas.paper.replay import ReplayError
from atlas.paper.types import Bar
from atlas.strategy.scalp_139_common import (
    FLAT,
    FORBIDDEN_CELLS,
    LONG,
    NO_ATR_TRAIL,
    NO_R_TP,
    NO_SL,
    NO_TIME_STOP,
    SHORT,
    Scalp139Signals,
    dual_ema_exit_series,
    regime_flip_series_1d_ema,
    regime_ok_series_1d_ema,
)
from atlas.strategy.scalp_139_d1_c2_nosl import precompute_d1_c2_nosl
from atlas.strategy.scalp_139_d2_alwaysin import precompute_d2_alwaysin
from atlas.strategy.scalp_139_d3_dual_ema import precompute_d3_dual_ema


H1 = 60 * 60_000
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


def _sig_long(n: int, **overrides: object) -> Scalp139Signals:
    base = dict(
        entry_ok=[False] * n,
        regime_flip=[False] * n,
        desired_side=[FLAT] * n,
    )
    base.update(overrides)
    return Scalp139Signals(**base)  # type: ignore[arg-type]


def test_phase_and_official_cells():
    assert PHASE1 == 139
    assert SOURCE == "public_md_scalp_139"
    assert OFFICIAL_CELLS == ("D1", "D2", "D3")
    assert set(CELL_SPECS) == set(OFFICIAL_CELLS)
    assert CELL_SPECS["D1"].family == "d1_c2_nosl"
    assert CELL_SPECS["D2"].family == "d2_alwaysin"
    assert CELL_SPECS["D3"].family == "d3_dual_ema"
    assert CELL_SPECS["D1"].sl_mode == "none"
    assert CELL_SPECS["D2"].sl_mode == "none"
    assert CELL_SPECS["D3"].sl_mode == "none"
    assert CELL_SPECS["D2"].allows_short is True
    assert CELL_SPECS["D1"].allows_short is False
    assert SCALP_START_EUR == 20.0
    assert TIME_STOP_DISABLED == 100_000
    assert TIME_STOP_DISABLED >= FULL_1H_TRADE_BARS_EXPECTED
    assert FULL_1H_TRADE_BARS_EXPECTED == 4416
    assert NO_TIME_STOP is True
    assert NO_SL is True
    assert EMA_1D == 21
    assert EMA_1D_SLOW == 50
    assert NO_R_TP is True
    assert NO_ATR_TRAIL is True


def test_reject_s4_and_dj_and_prior_cells():
    for bad in ("S4", "D", "J", "A", "S1", "S2", "C1", "C2", "C3", "N1", "L1"):
        with pytest.raises(ValueError):
            assert_sid_allowed(bad)
    assert "S4" in FORBIDDEN_CELLS
    assert "D" in FORBIDDEN_CELLS
    assert "J" in FORBIDDEN_CELLS


def test_candidate_ids():
    btc = candidate_id_for("D1", "BTC-USDT")
    eth = candidate_id_for("D2", "ETH-USDT")
    doge = candidate_id_for("D3", "DOGE-USDT")
    assert btc == "public_md_v1_139_d1_c2_nosl_btc_usdt_eur20"
    assert eth == "public_md_v1_139_d2_alwaysin_eth_usdt_eur20"
    assert doge == "public_md_v1_139_d3_dual_ema_doge_usdt_eur20"
    assert "1.5r" not in btc.lower()
    assert "s4" not in btc


def test_parent_baselines_honesty():
    assert PARENT_C2_138_FULL["BTC-USDT"]["n"] == 13
    assert PARENT_C2_138_FULL["BTC-USDT"]["exp"] == pytest.approx(1.15331755)
    assert PARENT_C2_138_FULL["ETH-USDT"]["terminal"] == pytest.approx(27.03224534)
    assert PARENT_C2_138_FULL["DOGE-USDT"]["exp"] == pytest.approx(0.5683572)
    assert PARENT_S2_135_FULL["BTC-USDT"]["n"] == 42
    assert PARENT_S2_135_FULL["BTC-USDT"]["exp"] == pytest.approx(0.15325586)
    assert PARENT_S2_135_FULL["ETH-USDT"]["terminal"] == pytest.approx(37.52870935)
    assert PARENT_S2_135_FULL["DOGE-USDT"]["exp"] == pytest.approx(0.3719052)
    assert BH_FULL_CITE["BTC-USDT"] == pytest.approx(43.17666206)
    assert BH_FULL_CITE["ETH-USDT"] == pytest.approx(45.16769469)
    assert BH_FULL_CITE["DOGE-USDT"] == pytest.approx(20.2301366)
    assert USDT_INSTS == ("BTC-USDT", "ETH-USDT", "DOGE-USDT")
    assert WINDOWS["FULL"][0] == "2020-07-01T00:00:00Z"


def test_d1_no_sl_entries_and_zero_sl_exits():
    n = 30
    bars = [_bar1h(i, 100, 101, 99, 100.5) for i in range(n)]
    entry_ok = [False] * n
    entry_ok[1] = True
    flip = [False] * n
    flip[10] = True
    sig = _sig_long(n, entry_ok=entry_ok, regime_flip=flip)
    out = walk_scalp_139_long_nosl(
        bars,
        sig,
        settings=_settings(),
        trade_start_ms=0,
        trade_end_ms=10**12,
        time_stop_bars=TIME_STOP_DISABLED,
    )
    assert out["n_long_entries"] == 1
    assert out["n_short_entries"] == 0
    assert out["n_sl_exits"] == 0
    assert out["exit_mix"]["sl"] == 0
    assert out["n_regime_exits"] == 1
    assert out["n_time_stop_exits"] == 0
    assert out["n_tp_exits"] == 0
    assert out["no_sl"] is True


def test_no_time_stop_even_after_504():
    n = 520
    bars = [_bar1h(i, 100, 101, 99, 100.5) for i in range(n)]
    entry_ok = [False] * n
    entry_ok[1] = True
    sig = _sig_long(n, entry_ok=entry_ok)
    out = walk_scalp_139_long_nosl(
        bars,
        sig,
        settings=_settings(),
        trade_start_ms=0,
        trade_end_ms=10**12,
        time_stop_bars=TIME_STOP_DISABLED,
    )
    assert out["n_time_stop_exits"] == 0
    assert out["exit_mix"]["time"] == 0
    assert out["n_long_entries"] == 1
    assert out["n_sl_exits"] == 0


def test_time_stop_cap_too_small_rejected():
    n = 10
    bars = [_bar1h(i, 100, 101, 99, 100.5) for i in range(n)]
    with pytest.raises(ReplayError, match="time_stop_bars"):
        walk_scalp_139_long_nosl(
            bars,
            _sig_long(n),
            settings=_settings(),
            trade_start_ms=0,
            trade_end_ms=10**12,
            time_stop_bars=504,
        )


def test_d2_shorts_and_flip_inplace():
    n = 40
    bars = [_bar1h(i, 100, 101, 99, 100.5) for i in range(n)]
    desired = [FLAT] * n
    for i in range(1, 15):
        desired[i] = LONG
    for i in range(15, 30):
        desired[i] = SHORT
    for i in range(30, n):
        desired[i] = LONG
    sig = _sig_long(n, desired_side=desired)
    out = walk_scalp_139_alwaysin(
        bars,
        sig,
        settings=_settings(),
        trade_start_ms=0,
        trade_end_ms=10**12,
        time_stop_bars=TIME_STOP_DISABLED,
    )
    assert out["n_short_entries"] >= 1
    assert out["n_long_entries"] >= 1
    assert out["n_sl_exits"] == 0
    assert out["exit_mix"]["sl"] == 0
    assert out["n_time_stop_exits"] == 0
    assert out["n_flip_inplace"] >= 1
    assert out["allows_short"] is True
    assert out["flip_in_place"] is True


def test_d3_requires_both_emas_for_exit():
    bars_1d: list[Bar] = []
    px = 100.0
    for i in range(60):
        o = px
        c = px + 1.0
        bars_1d.append(_bar1d(i, o, c + 1, o - 0.5, c))
        px = c
    # Day 60: moderate drop — may be < EMA21 but not both
    bars_1d.append(_bar1d(60, px, px + 0.5, 90.0, 95.0))
    # Day 61: deep drop below both EMAs
    bars_1d.append(_bar1d(61, 95.0, 96.0, 40.0, 40.0))

    n_1h = 62 * 24 + 2
    bars_1h = [_bar1h(i, 100, 101, 99, 100.5) for i in range(n_1h)]

    lt21 = regime_flip_series_1d_ema(bars_1h, bars_1d, ema_period=21)
    lt50 = regime_flip_series_1d_ema(bars_1h, bars_1d, ema_period=50)
    dual = dual_ema_exit_series(bars_1h, bars_1d, ema_fast=21, ema_slow=50)

    assert all(d == (a and b) for d, a, b in zip(dual, lt21, lt50, strict=True))

    day61_close_ms = 62 * D1
    idx61 = next(i for i, b in enumerate(bars_1h) if b.ts_close_ms == day61_close_ms)
    assert bars_1h[idx61 - 1].ts_close_ms < day61_close_ms
    # No lookahead: dual at hour before day61 close must not use day61 bar
    assert dual[idx61] == (lt21[idx61] and lt50[idx61])
    # Strict AND: dual never true when either leg is false
    assert not any(dual[i] and (not lt21[i] or not lt50[i]) for i in range(len(dual)))


def test_1d_ema21_no_lookahead():
    bars_1d: list[Bar] = []
    px = 100.0
    for i in range(25):
        o = px
        c = px + 1.0
        bars_1d.append(_bar1d(i, o, c + 1, o - 0.5, c))
        px = c
    bars_1d.append(_bar1d(25, px, px + 0.5, 50.0, 50.0))

    n_1h = 26 * 24 + 4
    bars_1h = [_bar1h(i, 100, 101, 99, 100.5) for i in range(n_1h)]
    flip = regime_flip_series_1d_ema(bars_1h, bars_1d, ema_period=21)
    day25_close_ms = 26 * D1
    last_hour = 25 * 24 + 23
    assert bars_1h[last_hour].ts_close_ms == day25_close_ms
    assert flip[last_hour - 1] is False
    assert flip[last_hour] is True
    ok = regime_ok_series_1d_ema(bars_1h, bars_1d, ema_period=21)
    assert ok[last_hour] is False


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


def test_precompute_lengths_and_no_sl_no_ts():
    bars_1h = [
        _bar1h(i, 100 + i * 0.1, 101 + i * 0.1, 99 + i * 0.1, 100.5 + i * 0.1)
        for i in range(120)
    ]
    bars_1d = [_bar1d(i, 100 + i, 110 + i, 90 + i, 108 + i) for i in range(60)]
    for fn, walker in (
        (precompute_d1_c2_nosl, "long"),
        (precompute_d2_alwaysin, "ai"),
        (precompute_d3_dual_ema, "long"),
    ):
        sig = fn(bars_1h, bars_1d)
        assert len(sig.entry_ok) == len(bars_1h)
        assert len(sig.regime_flip) == len(bars_1h)
        assert len(sig.desired_side) == len(bars_1h)
        if walker == "long":
            out = walk_scalp_139_long_nosl(
                bars_1h,
                sig,
                settings=_settings(),
                trade_start_ms=0,
                trade_end_ms=10**12,
                time_stop_bars=TIME_STOP_DISABLED,
            )
        else:
            out = walk_scalp_139_alwaysin(
                bars_1h,
                sig,
                settings=_settings(),
                trade_start_ms=0,
                trade_end_ms=10**12,
                time_stop_bars=TIME_STOP_DISABLED,
            )
        assert out["n_tp_exits"] == 0
        assert out["n_trail_exits"] == 0
        assert out["n_sl_exits"] == 0
        assert out["n_time_stop_exits"] == 0
