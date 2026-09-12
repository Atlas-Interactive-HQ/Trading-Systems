"""Unit tests: phase1/141 F1 hold-to-end / F2 sticky3 / F3 sticky dual."""

from __future__ import annotations

import pytest

from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.ema_eval import EmaBookSettings
from atlas.paper.public_md_scalp_141 import (
    BH_FULL_CITE,
    CELL_SPECS,
    EMA_1D,
    EMA_1D_SLOW,
    F2_STICKY_N,
    F3_STICKY_N,
    FULL_1H_TRADE_BARS_EXPECTED,
    OFFICIAL_CELLS,
    PARENT_D3_139_FULL,
    PARENT_E1_140_FULL,
    PHASE1,
    SOURCE,
    TIME_STOP_DISABLED,
    USDT_INSTS,
    WINDOWS,
    assert_sid_allowed,
    candidate_id_for,
    gate_for_full_cells,
    iso_to_ms,
    walk_scalp_141_long_nosl,
)
from atlas.paper.replay import ReplayError
from atlas.paper.types import Bar
from atlas.strategy.scalp_141_common import (
    FORBIDDEN_CELLS,
    NO_ATR_TRAIL,
    NO_R_TP,
    NO_SL,
    NO_TIME_STOP,
    Scalp141Signals,
    first_full_1d_seed_series,
    lt_ema_predicate_1d,
    sticky_consecutive_from_1d_flags,
    sticky_dual_ema_exit_series,
    sticky_lt_ema_exit_series,
)
from atlas.strategy.scalp_141_f1_holdend import precompute_f1_holdend
from atlas.strategy.scalp_141_f2_sticky3 import precompute_f2_sticky3
from atlas.strategy.scalp_141_f3_sticky_dual import precompute_f3_sticky_dual


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


def _sig(n: int, **overrides: object) -> Scalp141Signals:
    base = dict(
        entry_ok=[False] * n,
        regime_flip=[False] * n,
        seed_fired=[False] * n,
    )
    base.update(overrides)
    return Scalp141Signals(**base)  # type: ignore[arg-type]


def test_phase_and_official_cells():
    assert PHASE1 == 141
    assert SOURCE == "public_md_scalp_141"
    assert OFFICIAL_CELLS == ("F1", "F2", "F3")
    assert set(CELL_SPECS) == set(OFFICIAL_CELLS)
    assert CELL_SPECS["F1"].family == "f1_holdend"
    assert CELL_SPECS["F2"].family == "f2_sticky3"
    assert CELL_SPECS["F3"].family == "f3_sticky_dual"
    assert CELL_SPECS["F1"].hold_to_end is True
    assert CELL_SPECS["F2"].sticky_n == 3
    assert CELL_SPECS["F3"].sticky_n == 2
    assert F2_STICKY_N == 3
    assert F3_STICKY_N == 2
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


def test_reject_forbidden_and_prior_cells():
    for bad in ("S4", "D", "J", "A", "S1", "C1", "D1", "D2", "D3", "E1", "E2", "E3"):
        with pytest.raises(ValueError):
            assert_sid_allowed(bad)
    assert "D2" in FORBIDDEN_CELLS
    assert "E1" in FORBIDDEN_CELLS


def test_candidate_ids():
    btc = candidate_id_for("F1", "BTC-USDT")
    eth = candidate_id_for("F2", "ETH-USDT")
    doge = candidate_id_for("F3", "DOGE-USDT")
    assert btc == "public_md_v1_141_f1_holdend_btc_usdt_eur20"
    assert eth == "public_md_v1_141_f2_sticky3_eth_usdt_eur20"
    assert doge == "public_md_v1_141_f3_sticky_dual_doge_usdt_eur20"


def test_parent_honesty_and_bh():
    assert PARENT_E1_140_FULL["BTC-USDT"]["n"] == 5
    assert PARENT_E1_140_FULL["BTC-USDT"]["exp"] == pytest.approx(0.24547621)
    assert PARENT_E1_140_FULL["DOGE-USDT"]["terminal"] == pytest.approx(22.74117359)
    assert PARENT_D3_139_FULL["BTC-USDT"]["n"] == 4
    assert PARENT_D3_139_FULL["BTC-USDT"]["exp"] == pytest.approx(0.44113722)
    assert PARENT_D3_139_FULL["ETH-USDT"]["terminal"] == pytest.approx(29.69515514)
    assert BH_FULL_CITE["BTC-USDT"] == pytest.approx(43.17666206)
    assert BH_FULL_CITE["ETH-USDT"] == pytest.approx(45.16769469)
    assert BH_FULL_CITE["DOGE-USDT"] == pytest.approx(20.2301366)
    assert USDT_INSTS == ("BTC-USDT", "ETH-USDT", "DOGE-USDT")
    assert WINDOWS["FULL"][0] == "2020-07-01T00:00:00Z"


def test_seed_fires_when_first_full_1d_already_above():
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
    first_full_1d = next(b for b in bars_1d if b.ts_open_ms >= full_start_ms)
    idx = next(
        i for i, b in enumerate(bars_1h) if b.ts_close_ms >= first_full_1d.ts_close_ms
    )
    assert seed[idx] is True
    assert seed[idx - 1] is False
    sig = precompute_f1_holdend(
        bars_1h, bars_1d, full_start_ms=full_start_ms, full_end_ms=full_end_ms
    )
    assert sig.seed_fired[idx] is True
    assert sig.entry_ok[idx] is True
    assert all(x is False for x in sig.regime_flip)


def test_f1_no_mid_window_exit_only_forced_end():
    n = 40
    bars = [_bar1h(i, 100 + i * 0.1, 101 + i * 0.1, 99 + i * 0.1, 100.5 + i * 0.1) for i in range(n)]
    entry_ok = [False] * n
    entry_ok[1] = True
    flip = [True] * n  # would exit if regime allowed
    out = walk_scalp_141_long_nosl(
        bars,
        _sig(n, entry_ok=entry_ok, regime_flip=flip),
        settings=_settings(),
        trade_start_ms=0,
        trade_end_ms=n * H1,
        time_stop_bars=TIME_STOP_DISABLED,
        allow_regime_exit=False,
    )
    assert out["n_long_entries"] == 1
    assert out["n_short_entries"] == 0
    assert out["n_regime_exits"] == 0
    assert out["n_sl_exits"] == 0
    assert out["n_time_stop_exits"] == 0
    assert out["exit_mix"]["time"] == 0
    assert out["exit_mix"]["sl"] == 0
    assert out["n_forced_end_exits"] == 1
    assert out["exit_mix"]["forced_end"] == 1
    assert out["n_trades"] == 1
    assert out["open_position_at_end"] is False


def test_f2_needs_three_consecutive_not_two():
    # Warm EMA21, then crash hard so close < EMA for sticky days.
    bars_1d: list[Bar] = []
    px = 100.0
    for i in range(30):
        o = px
        c = px + 1.0
        bars_1d.append(_bar1d(i, o, c + 1, o - 0.5, c))
        px = c
    # two crash days — sticky3 must stay False (only 2)
    for i in range(30, 32):
        o = px
        c = 10.0  # far below EMA21
        bars_1d.append(_bar1d(i, o, o + 0.5, c - 1, c))
        px = c
    # bounce day resets streak (close back above EMA)
    o = px
    c = 200.0
    bars_1d.append(_bar1d(32, o, c + 1, o - 0.5, c))
    px = c
    # three consecutive crash days
    for i in range(33, 36):
        o = px
        c = 5.0
        bars_1d.append(_bar1d(i, o, o + 0.5, c - 1, c))
        px = c
    n_1h = 40 * 24
    bars_1h = [_bar1h(i, 100, 101, 99, 100.5) for i in range(n_1h)]
    day = lt_ema_predicate_1d(bars_1d, ema_period=21)
    assert day[30] is True and day[31] is True and day[32] is False
    assert day[33] is True and day[34] is True and day[35] is True
    sticky2 = sticky_consecutive_from_1d_flags(bars_1h, bars_1d, day, n_consec=2)
    sticky3 = sticky_lt_ema_exit_series(bars_1h, bars_1d, ema_period=21, n_consec=3)
    day31_close = 32 * D1  # close of day index 31
    idx_after_2 = next(i for i, b in enumerate(bars_1h) if b.ts_close_ms >= day31_close)
    assert sticky2[idx_after_2] is True
    assert sticky3[idx_after_2] is False
    day35_close = 36 * D1
    idx_after_3 = next(i for i, b in enumerate(bars_1h) if b.ts_close_ms >= day35_close)
    assert sticky3[idx_after_3] is True
    assert sticky3[idx_after_3 - 1] is False  # no lookahead into day 35 before close


def test_f3_needs_two_dual_not_one():
    bars_1d: list[Bar] = []
    px = 100.0
    for i in range(60):
        o = px
        c = px + 1.0
        bars_1d.append(_bar1d(i, o, c + 1, o - 0.5, c))
        px = c
    # one dual-crash day — sticky2 dual must stay False
    o = px
    c = 1.0
    bars_1d.append(_bar1d(60, o, o + 0.5, c - 0.1, c))
    px = c
    # second dual-crash day
    o = px
    c = 1.0
    bars_1d.append(_bar1d(61, o, o + 0.5, c - 0.1, c))
    px = c
    n_1h = 65 * 24
    bars_1h = [_bar1h(i, 100, 101, 99, 100.5) for i in range(n_1h)]
    sticky1 = sticky_dual_ema_exit_series(
        bars_1h, bars_1d, ema_fast=21, ema_slow=50, n_consec=1
    )
    sticky2 = sticky_dual_ema_exit_series(
        bars_1h, bars_1d, ema_fast=21, ema_slow=50, n_consec=2
    )
    day60_close = 61 * D1
    idx1 = next(i for i, b in enumerate(bars_1h) if b.ts_close_ms >= day60_close)
    assert sticky1[idx1] is True
    assert sticky2[idx1] is False
    day61_close = 62 * D1
    idx2 = next(i for i, b in enumerate(bars_1h) if b.ts_close_ms >= day61_close)
    assert sticky2[idx2] is True


def test_regime_exit_then_forced_end_mix_and_no_sl_no_ts():
    n = 30
    bars = [_bar1h(i, 100, 101, 99, 100.5) for i in range(n)]
    entry_ok = [False] * n
    entry_ok[1] = True
    flip = [False] * n
    flip[10] = True
    out = walk_scalp_141_long_nosl(
        bars,
        _sig(n, entry_ok=entry_ok, regime_flip=flip),
        settings=_settings(),
        trade_start_ms=0,
        trade_end_ms=10**12,
        time_stop_bars=TIME_STOP_DISABLED,
        allow_regime_exit=True,
    )
    assert out["n_long_entries"] == 1
    assert out["n_short_entries"] == 0
    assert out["n_sl_exits"] == 0
    assert out["exit_mix"]["sl"] == 0
    assert out["n_regime_exits"] == 1
    assert out["n_time_stop_exits"] == 0
    assert out["exit_mix"]["time"] == 0
    assert out["n_tp_exits"] == 0
    # After regime exit, flat to end → no forced_end
    assert out["n_forced_end_exits"] == 0


def test_no_time_stop_even_after_504():
    n = 520
    bars = [_bar1h(i, 100, 101, 99, 100.5) for i in range(n)]
    entry_ok = [False] * n
    entry_ok[1] = True
    out = walk_scalp_141_long_nosl(
        bars,
        _sig(n, entry_ok=entry_ok),
        settings=_settings(),
        trade_start_ms=0,
        trade_end_ms=n * H1,
        time_stop_bars=TIME_STOP_DISABLED,
        allow_regime_exit=True,
    )
    assert out["n_time_stop_exits"] == 0
    assert out["exit_mix"]["time"] == 0
    assert out["n_long_entries"] == 1
    assert out["n_sl_exits"] == 0
    assert out["n_forced_end_exits"] == 1


def test_time_stop_cap_too_small_rejected():
    n = 10
    bars = [_bar1h(i, 100, 101, 99, 100.5) for i in range(n)]
    with pytest.raises(ReplayError, match="time_stop_bars"):
        walk_scalp_141_long_nosl(
            bars,
            _sig(n),
            settings=_settings(),
            trade_start_ms=0,
            trade_end_ms=10**12,
            time_stop_bars=504,
        )


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


def test_precompute_lengths_no_shorts_no_sl_no_ts():
    bars_1h = [
        _bar1h(i, 100 + i * 0.1, 101 + i * 0.1, 99 + i * 0.1, 100.5 + i * 0.1)
        for i in range(120)
    ]
    bars_1d = [_bar1d(i, 100 + i, 110 + i, 90 + i, 108 + i) for i in range(110)]
    full_start = 30 * D1
    full_end = 100 * D1
    for sid, sig in (
        (
            "F1",
            precompute_f1_holdend(
                bars_1h, bars_1d, full_start_ms=full_start, full_end_ms=full_end
            ),
        ),
        (
            "F2",
            precompute_f2_sticky3(
                bars_1h, bars_1d, full_start_ms=full_start, full_end_ms=full_end
            ),
        ),
        (
            "F3",
            precompute_f3_sticky_dual(
                bars_1h, bars_1d, full_start_ms=full_start, full_end_ms=full_end
            ),
        ),
    ):
        assert len(sig.entry_ok) == len(bars_1h)
        assert len(sig.regime_flip) == len(bars_1h)
        assert len(sig.seed_fired) == len(bars_1h)
        if sid == "F1":
            assert all(x is False for x in sig.regime_flip)
        out = walk_scalp_141_long_nosl(
            bars_1h,
            sig,
            settings=_settings(),
            trade_start_ms=0,
            trade_end_ms=120 * H1,
            time_stop_bars=TIME_STOP_DISABLED,
            allow_regime_exit=(sid != "F1"),
        )
        assert out["n_tp_exits"] == 0
        assert out["n_trail_exits"] == 0
        assert out["n_sl_exits"] == 0
        assert out["n_time_stop_exits"] == 0
        assert out["n_short_entries"] == 0


def test_full_window_iso_ms():
    assert iso_to_ms(WINDOWS["FULL"][0]) == 1593561600000
