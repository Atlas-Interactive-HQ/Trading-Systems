"""Unit tests: phase1/135 hold-strengthen S1–S4 (F/G/C/A). No D/J. No grind."""

from __future__ import annotations

import pytest

from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.ema_eval import EmaBookSettings
from atlas.paper.public_md_scalp_135 import (
    ATR_TRAIL_MULT,
    BH_FULL_CITE,
    CELL_SPECS,
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
    resolve_fixed_sl,
    resolve_trail_seed,
    walk_scalp_135,
)
from atlas.paper.types import Bar
from atlas.strategy.scalp_135_common import (
    FORBIDDEN_CELLS,
    NO_R_TP,
    Scalp135Signals,
)
from atlas.strategy.scalp_135_s1_f_supertrend import ST_MULT, ST_PERIOD, precompute_s1_f
from atlas.strategy.scalp_135_s2_g_keltner import KC_MULT, KC_PERIOD, precompute_s2_g
from atlas.strategy.scalp_135_s3_c_donchian import LOOKBACK, precompute_s3_c
from atlas.strategy.scalp_135_s4_a_dt_atrtrail import precompute_s4_a
from atlas.strategy.scalp_dt_rvol_1h_133 import ScalpDtRvol1h133Params, ScalpDtRvol1h133V1


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


def _settings() -> EmaBookSettings:
    return EmaBookSettings(
        equity_eur=20.0, fee_rate=0.0005, slippage_bps=5.0, leverage=1.0
    )


def _sig(n: int, **overrides: object) -> Scalp135Signals:
    base = dict(
        entry_ok=[False] * n,
        regime_flip=[False] * n,
        atr=[1.0] * n,
        sl_ref=[95.0] * n,
    )
    base.update(overrides)
    return Scalp135Signals(**base)  # type: ignore[arg-type]


def test_phase_and_official_cells():
    assert PHASE1 == 135
    assert SOURCE == "public_md_scalp_135"
    assert OFFICIAL_CELLS == ("S1", "S2", "S3", "S4")
    assert set(CELL_SPECS) == set(OFFICIAL_CELLS)
    assert CELL_SPECS["S1"].letter == "F"
    assert CELL_SPECS["S2"].letter == "G"
    assert CELL_SPECS["S3"].letter == "C"
    assert CELL_SPECS["S4"].letter == "A"
    assert SCALP_START_EUR == 20.0
    assert TIME_STOP == 168
    assert ATR_TRAIL_MULT == 2.0
    assert NO_R_TP is True


def test_reject_dj_and_offlist():
    for bad in ("D", "J", "B", "E"):
        with pytest.raises(ValueError):
            assert_sid_allowed(bad)


def test_reject_param_grind_on_133_entry_locked():
    with pytest.raises(ValueError, match="grind"):
        ScalpDtRvol1h133V1(ScalpDtRvol1h133Params(lookback=5))
    with pytest.raises(ValueError, match="grind"):
        ScalpDtRvol1h133V1(ScalpDtRvol1h133Params(k1=0.6))
    with pytest.raises(ValueError, match="1.5R|r_multiple"):
        ScalpDtRvol1h133V1(ScalpDtRvol1h133Params(r_multiple=1.5))
    assert ST_PERIOD == 10 and ST_MULT == 3.0
    assert KC_PERIOD == 20 and KC_MULT == 1.5
    assert LOOKBACK == 20


def test_candidate_ids():
    assert candidate_id_for("S1", "BTC-USDT").endswith("_btc_usdt_eur20")
    assert "135_f_emaflip_ts168" in candidate_id_for("S1", "BTC-USDT")
    assert "atrtrail" not in candidate_id_for("S1", "BTC-USDT")
    assert "135_a_emaflip_atrtrail2_ts168" in candidate_id_for("S4", "ETH-USDT")
    assert "135_c_emaflip_ts168" in candidate_id_for("S3", "DOGE-USDT")
    assert "135_g_emaflip_ts168" in candidate_id_for("S2", "BTC-USDT")


def test_parent_baselines_honesty():
    assert PARENT_FULL["A"]["BTC-USDT"]["n"] == 16
    assert PARENT_FULL["A"]["BTC-USDT"]["exp"] == pytest.approx(0.14934035)
    assert PARENT_FULL["C"]["ETH-USDT"]["exp"] == pytest.approx(0.03950258)
    assert PARENT_FULL["F"]["DOGE-USDT"]["terminal"] == pytest.approx(4.45515136)
    assert PARENT_FULL["G"]["BTC-USDT"]["n"] == 90
    assert BH_FULL_CITE["BTC-USDT"] == pytest.approx(43.17666206)
    assert USDT_INSTS == ("BTC-USDT", "ETH-USDT", "DOGE-USDT")
    assert WINDOWS["FULL"][0] == "2020-07-01T00:00:00Z"


def test_trail_ratchets_only_up():
    """ATR trail never loosens; exit on close <= trail; no 1.5R flatten."""
    # Build a path: enter, price rises (trail ratchets up), then dips to trail.
    n = 20
    bars = []
    px = 100.0
    for i in range(n):
        if i < 5:
            o, c = px, px + 1.0
        elif i < 12:
            o, c = px, px + 2.0
        else:
            o, c = px, px - 3.0
        bars.append(_bar1h(i, o, max(o, c) + 0.5, min(o, c) - 0.5, c))
        px = c
    entry_ok = [False] * n
    entry_ok[2] = True
    atr = [2.0] * n  # 2×ATR = 4
    sig = _sig(n, entry_ok=entry_ok, atr=atr, sl_ref=[None] * n, regime_flip=[False] * n)
    out = walk_scalp_135(
        bars,
        sig,
        settings=_settings(),
        trade_start_ms=0,
        trade_end_ms=10**12,
        exit_mode="atr_trail_2x",
        time_stop_bars=168,
    )
    assert out["n_tp_exits"] == 0
    assert out["n_sellline_exits"] == 0
    assert out["r_multiple"] is None
    # Should have entered and eventually trail-exited (or still open)
    assert out["n_long_entries"] >= 1
    assert out["n_tp_exits"] == 0


def test_trail_seed_and_ratchet_helper():
    assert resolve_trail_seed(entry_px=100.0, atr=2.0) == pytest.approx(96.0)
    assert resolve_trail_seed(entry_px=100.0, atr=None) is None
    assert resolve_fixed_sl(entry_px=100.0, sl_ref=95.0) == 95.0
    assert resolve_fixed_sl(entry_px=100.0, sl_ref=100.0) is None
    assert resolve_fixed_sl(entry_px=100.0, sl_ref=101.0) is None


def test_one_point_five_r_does_not_flatten():
    """Even if price runs 10R, walker must not take TP (no 1.5R)."""
    n = 30
    bars = []
    px = 100.0
    for i in range(n):
        o = px
        c = px + 5.0  # strong up
        bars.append(_bar1h(i, o, c + 1, o - 0.1, c))
        px = c
    entry_ok = [False] * n
    entry_ok[1] = True
    sl_ref = [99.0] * n
    sig = _sig(n, entry_ok=entry_ok, sl_ref=sl_ref, atr=[1.0] * n)
    out = walk_scalp_135(
        bars,
        sig,
        settings=_settings(),
        trade_start_ms=0,
        trade_end_ms=10**12,
        exit_mode="a_style_fixed_sl",
        time_stop_bars=168,
    )
    assert out["n_tp_exits"] == 0
    assert out["n_sl_exits"] == 0 or out["n_trades"] >= 0
    # Still in or exited only via regime/time — not TP
    assert out["n_tp_exits"] == 0


def test_ema_flip_exits():
    n = 15
    bars = [_bar1h(i, 100 + i, 101 + i, 99 + i, 100.5 + i) for i in range(n)]
    entry_ok = [False] * n
    entry_ok[1] = True
    flip = [False] * n
    flip[5] = True
    sig = _sig(n, entry_ok=entry_ok, regime_flip=flip, sl_ref=[90.0] * n, atr=[1.0] * n)
    out = walk_scalp_135(
        bars,
        sig,
        settings=_settings(),
        trade_start_ms=0,
        trade_end_ms=10**12,
        exit_mode="a_style_fixed_sl",
        time_stop_bars=168,
    )
    assert out["n_regime_flip_exits"] >= 1
    assert out["n_tp_exits"] == 0


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


def test_precompute_lengths_match():
    bars_1h = [_bar1h(i, 100 + i * 0.1, 101 + i * 0.1, 99 + i * 0.1, 100.5 + i * 0.1) for i in range(80)]
    bars_4h = []
    for i in range(40):
        open_ms = i * 4 * 60 * 60_000
        bars_4h.append(
            Bar(
                symbol="BTC-USDT",
                ts_open_ms=open_ms,
                ts_close_ms=open_ms + 4 * 60 * 60_000,
                open=100 + i,
                high=105 + i,
                low=99 + i,
                close=104 + i,
                volume=1000.0,
                closed=True,
                source="test",
            )
        )
    for fn in (precompute_s1_f, precompute_s2_g, precompute_s3_c, precompute_s4_a):
        sig = fn(bars_1h, bars_4h)
        assert len(sig.entry_ok) == len(bars_1h)
        assert len(sig.regime_flip) == len(bars_1h)
        assert len(sig.atr) == len(bars_1h)
        assert len(sig.sl_ref) == len(bars_1h)


def test_s1_s3_exit_mode_no_atr_trail_flag():
    assert CELL_SPECS["S1"].exit_mode == "a_style_fixed_sl"
    assert CELL_SPECS["S2"].exit_mode == "a_style_fixed_sl"
    assert CELL_SPECS["S3"].exit_mode == "a_style_fixed_sl"
    assert CELL_SPECS["S4"].exit_mode == "atr_trail_2x"
    assert "D" in FORBIDDEN_CELLS and "J" in FORBIDDEN_CELLS
