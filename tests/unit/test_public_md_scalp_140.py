"""Unit tests: phase1/140 E1 seed / E2 EMA12 / E3 EMA50+100."""

from __future__ import annotations

import pytest

from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.ema_eval import EmaBookSettings
from atlas.paper.public_md_scalp_140 import (
    BH_FULL_CITE,
    CELL_SPECS,
    EMA_1D,
    EMA_1D_FAST_E2,
    EMA_1D_SLOW,
    EMA_1D_XSlow,
    FULL_1H_TRADE_BARS_EXPECTED,
    OFFICIAL_CELLS,
    PARENT_D3_139_FULL,
    PHASE1,
    SOURCE,
    TIME_STOP_DISABLED,
    USDT_INSTS,
    WINDOWS,
    assert_sid_allowed,
    candidate_id_for,
    gate_for_full_cells,
    iso_to_ms,
    walk_scalp_140_long_nosl,
)
from atlas.paper.replay import ReplayError
from atlas.paper.types import Bar
from atlas.strategy.scalp_140_common import (
    FORBIDDEN_CELLS,
    NO_ATR_TRAIL,
    NO_R_TP,
    NO_SL,
    NO_TIME_STOP,
    Scalp140Signals,
    dual_ema_exit_series,
    first_full_1d_seed_series,
    regime_flip_series_1d_ema,
    regime_ok_series_1d_ema,
)
from atlas.strategy.scalp_140_e1_seed import precompute_e1_seed
from atlas.strategy.scalp_140_e2_ema12 import precompute_e2_ema12
from atlas.strategy.scalp_140_e3_ema50_100 import precompute_e3_ema50_100


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


def _sig(n: int, **overrides: object) -> Scalp140Signals:
    base = dict(
        entry_ok=[False] * n,
        regime_flip=[False] * n,
        seed_fired=[False] * n,
    )
    base.update(overrides)
    return Scalp140Signals(**base)  # type: ignore[arg-type]


def test_phase_and_official_cells():
    assert PHASE1 == 140
    assert SOURCE == "public_md_scalp_140"
    assert OFFICIAL_CELLS == ("E1", "E2", "E3")
    assert set(CELL_SPECS) == set(OFFICIAL_CELLS)
    assert CELL_SPECS["E1"].family == "e1_seed"
    assert CELL_SPECS["E2"].family == "e2_ema12"
    assert CELL_SPECS["E3"].family == "e3_ema50_100"
    assert CELL_SPECS["E1"].uses_seed is True
    assert CELL_SPECS["E2"].uses_seed is False
    assert CELL_SPECS["E3"].uses_seed is False
    assert CELL_SPECS["E1"].sl_mode == "none"
    assert CELL_SPECS["E2"].entry_ema == 12
    assert CELL_SPECS["E3"].exit_ema_fast == 50
    assert CELL_SPECS["E3"].exit_ema_slow == 100
    assert SCALP_START_EUR == 20.0
    assert TIME_STOP_DISABLED == 100_000
    assert TIME_STOP_DISABLED >= FULL_1H_TRADE_BARS_EXPECTED
    assert FULL_1H_TRADE_BARS_EXPECTED == 4416
    assert NO_TIME_STOP is True
    assert NO_SL is True
    assert EMA_1D == 21
    assert EMA_1D_FAST_E2 == 12
    assert EMA_1D_SLOW == 50
    assert EMA_1D_XSlow == 100
    assert NO_R_TP is True
    assert NO_ATR_TRAIL is True


def test_reject_forbidden_and_d2_shorts_cells():
    for bad in ("S4", "D", "J", "A", "S1", "S2", "C1", "C2", "D1", "D2", "D3"):
        with pytest.raises(ValueError):
            assert_sid_allowed(bad)
    assert "D2" in FORBIDDEN_CELLS
    assert "S4" in FORBIDDEN_CELLS


def test_candidate_ids():
    btc = candidate_id_for("E1", "BTC-USDT")
    eth = candidate_id_for("E2", "ETH-USDT")
    doge = candidate_id_for("E3", "DOGE-USDT")
    assert btc == "public_md_v1_140_e1_seed_btc_usdt_eur20"
    assert eth == "public_md_v1_140_e2_ema12_eth_usdt_eur20"
    assert doge == "public_md_v1_140_e3_ema50_100_doge_usdt_eur20"


def test_parent_d3_honesty_and_bh():
    assert PARENT_D3_139_FULL["BTC-USDT"]["n"] == 4
    assert PARENT_D3_139_FULL["BTC-USDT"]["exp"] == pytest.approx(0.44113722)
    assert PARENT_D3_139_FULL["ETH-USDT"]["terminal"] == pytest.approx(29.69515514)
    assert PARENT_D3_139_FULL["DOGE-USDT"]["exp"] == pytest.approx(2.06727372)
    assert BH_FULL_CITE["BTC-USDT"] == pytest.approx(43.17666206)
    assert BH_FULL_CITE["ETH-USDT"] == pytest.approx(45.16769469)
    assert BH_FULL_CITE["DOGE-USDT"] == pytest.approx(20.2301366)
    assert USDT_INSTS == ("BTC-USDT", "ETH-USDT", "DOGE-USDT")
    assert WINDOWS["FULL"][0] == "2020-07-01T00:00:00Z"


def test_e1_seed_fires_when_first_full_1d_already_above():
    # Build 30 rising days so EMA21 is warm and close > EMA at FULL start day.
    bars_1d: list[Bar] = []
    px = 100.0
    for i in range(40):
        o = px
        c = px + 1.0
        bars_1d.append(_bar1d(i, o, c + 1, o - 0.5, c))
        px = c
    full_start_day = 30
    full_start_ms = full_start_day * D1
    full_end_ms = 50 * D1
    n_1h = 45 * 24
    bars_1h = [_bar1h(i, 100, 101, 99, 100.5) for i in range(n_1h)]
    seed = first_full_1d_seed_series(
        bars_1h,
        bars_1d,
        ema_period=21,
        full_start_ms=full_start_ms,
        full_end_ms=full_end_ms,
    )
    assert any(seed)
    # Seed lands on the 1H that first observes first FULL 1D close.
    first_full_1d = next(b for b in bars_1d if b.ts_open_ms >= full_start_ms)
    idx = next(i for i, b in enumerate(bars_1h) if b.ts_close_ms >= first_full_1d.ts_close_ms)
    assert seed[idx] is True
    assert seed[idx - 1] is False
    sig = precompute_e1_seed(
        bars_1h, bars_1d, full_start_ms=full_start_ms, full_end_ms=full_end_ms
    )
    assert sig.seed_fired[idx] is True
    assert sig.entry_ok[idx] is True


def test_e1_seed_cold_ema_fail_closed():
    # Only 5 daily bars — EMA21 cold → no seed.
    bars_1d = [_bar1d(i, 100 + i, 110 + i, 90 + i, 108 + i) for i in range(5)]
    bars_1h = [_bar1h(i, 100, 101, 99, 100.5) for i in range(10 * 24)]
    seed = first_full_1d_seed_series(
        bars_1h,
        bars_1d,
        ema_period=21,
        full_start_ms=0,
        full_end_ms=10 * D1,
    )
    assert seed == [False] * len(bars_1h)


def test_no_sl_no_shorts_no_time_stop():
    n = 30
    bars = [_bar1h(i, 100, 101, 99, 100.5) for i in range(n)]
    entry_ok = [False] * n
    entry_ok[1] = True
    flip = [False] * n
    flip[10] = True
    out = walk_scalp_140_long_nosl(
        bars,
        _sig(n, entry_ok=entry_ok, regime_flip=flip),
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
    out = walk_scalp_140_long_nosl(
        bars,
        _sig(n, entry_ok=entry_ok),
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
        walk_scalp_140_long_nosl(
            bars,
            _sig(n),
            settings=_settings(),
            trade_start_ms=0,
            trade_end_ms=10**12,
            time_stop_bars=504,
        )


def test_e2_ema12_entry_vs_ema21():
    bars_1d: list[Bar] = []
    px = 100.0
    for i in range(30):
        o = px
        c = px + 0.5
        bars_1d.append(_bar1d(i, o, c + 1, o - 0.5, c))
        px = c
    # Sharper drop then bounce that may clear EMA12 before EMA21.
    bars_1d.append(_bar1d(30, px, px + 0.5, 70.0, 72.0))
    bars_1d.append(_bar1d(31, 72.0, 85.0, 71.0, 84.0))
    n_1h = 35 * 24
    bars_1h = [_bar1h(i, 100, 101, 99, 100.5) for i in range(n_1h)]
    ok12 = regime_ok_series_1d_ema(bars_1h, bars_1d, ema_period=12)
    ok21 = regime_ok_series_1d_ema(bars_1h, bars_1d, ema_period=21)
    # At least as many (usually more) EMA12-true hours than EMA21-true.
    assert sum(ok12) >= sum(ok21)
    sig = precompute_e2_ema12(bars_1h, bars_1d)
    assert sig.entry_ok == ok12
    assert all(not x for x in sig.seed_fired)


def test_e3_dual_ema50_100_and_no_lookahead():
    bars_1d: list[Bar] = []
    px = 100.0
    for i in range(120):
        o = px
        c = px + 1.0
        bars_1d.append(_bar1d(i, o, c + 1, o - 0.5, c))
        px = c
    bars_1d.append(_bar1d(120, px, px + 0.5, 40.0, 40.0))
    n_1h = 122 * 24 + 2
    bars_1h = [_bar1h(i, 100, 101, 99, 100.5) for i in range(n_1h)]
    lt50 = regime_flip_series_1d_ema(bars_1h, bars_1d, ema_period=50)
    lt100 = regime_flip_series_1d_ema(bars_1h, bars_1d, ema_period=100)
    dual = dual_ema_exit_series(bars_1h, bars_1d, ema_fast=50, ema_slow=100)
    assert all(d == (a and b) for d, a, b in zip(dual, lt50, lt100, strict=True))
    day_close_ms = 121 * D1
    last_hour = 120 * 24 + 23
    assert bars_1h[last_hour].ts_close_ms == day_close_ms
    assert dual[last_hour - 1] is False  # no lookahead
    sig = precompute_e3_ema50_100(bars_1h, bars_1d)
    assert sig.regime_flip == dual


def test_ema100_cold_entry_false():
    # <100 daily bars → EMA100 exit legs stay False (cold); entry EMA21 may warm.
    bars_1d = [_bar1d(i, 100 + i, 110 + i, 90 + i, 108 + i) for i in range(50)]
    bars_1h = [_bar1h(i, 100, 101, 99, 100.5) for i in range(55 * 24)]
    lt100 = regime_flip_series_1d_ema(bars_1h, bars_1d, ema_period=100)
    assert all(x is False for x in lt100)
    sig = precompute_e3_ema50_100(bars_1h, bars_1d)
    assert all(x is False for x in sig.regime_flip)


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
    bars_1d = [_bar1d(i, 100 + i, 110 + i, 90 + i, 108 + i) for i in range(110)]
    full_start = 30 * D1
    full_end = 100 * D1
    for sig in (
        precompute_e1_seed(
            bars_1h, bars_1d, full_start_ms=full_start, full_end_ms=full_end
        ),
        precompute_e2_ema12(bars_1h, bars_1d),
        precompute_e3_ema50_100(bars_1h, bars_1d),
    ):
        assert len(sig.entry_ok) == len(bars_1h)
        assert len(sig.regime_flip) == len(bars_1h)
        assert len(sig.seed_fired) == len(bars_1h)
        out = walk_scalp_140_long_nosl(
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
        assert out["n_short_entries"] == 0


def test_full_window_iso_ms():
    assert iso_to_ms(WINDOWS["FULL"][0]) == 1593561600000
