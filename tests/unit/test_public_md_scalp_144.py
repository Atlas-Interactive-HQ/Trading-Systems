"""Unit tests for #144 T1/T2/T3 stretch rules (no network)."""

from __future__ import annotations

from atlas.paper.ema_eval import EmaBookSettings
from atlas.paper.public_md_scalp_144 import (
    CELL_R_MULTIPLE,
    CELL_RVOL_GATE,
    CELL_USE_TP,
    OFFICIAL_CELLS,
    walk_notebook_stretch_cell,
)
from atlas.paper.types import Bar
from atlas.strategy.scalp_142_notebook import (
    LONG,
    NotebookSetup,
    PIVOT_N,
    RVOL_GATE,
    build_tf_bundle,
    discover_setups,
)


def _bar(
    i: int,
    *,
    o=100.0,
    h=101.0,
    l=99.0,
    c=100.0,
    v=1.0,
    tf_ms=60_000,
    symbol="BTC-USDT",
) -> Bar:
    t0 = 1_590_969_600_000 + i * tf_ms
    return Bar(
        symbol=symbol,
        ts_open_ms=t0,
        ts_close_ms=t0 + tf_ms - 1,
        open=o,
        high=h,
        low=l,
        close=c,
        volume=v,
        closed=True,
    )


def test_official_cells_and_params() -> None:
    assert OFFICIAL_CELLS == ("T1", "T2", "T3")
    assert CELL_R_MULTIPLE["T1"] == 4.0
    assert CELL_R_MULTIPLE["T2"] is None
    assert CELL_R_MULTIPLE["T3"] == 3.0
    assert CELL_USE_TP["T1"] is True
    assert CELL_USE_TP["T2"] is False
    assert CELL_USE_TP["T3"] is True
    assert CELL_RVOL_GATE["T1"] == float(RVOL_GATE) == 1.0
    assert CELL_RVOL_GATE["T2"] == 1.0
    assert CELL_RVOL_GATE["T3"] == 0.8
    assert PIVOT_N == 3


def test_t2_no_tp_zero_tp_exits() -> None:
    """T2: use_tp=False → n_tp stays 0 even if price runs far."""
    bars_1m = []
    for i in range(40):
        if i == 15:
            bars_1m.append(_bar(i, o=100.0, h=100.5, l=99.5, c=100.2, tf_ms=60_000))
        elif i == 20:
            # huge run that would hit any TP — must NOT count as TP
            bars_1m.append(_bar(i, o=100.0, h=200.0, l=99.0, c=150.0, tf_ms=60_000))
        elif i == 25:
            # SL hit
            bars_1m.append(_bar(i, o=100.0, h=100.5, l=90.0, c=95.0, tf_ms=60_000))
        else:
            bars_1m.append(_bar(i, o=100.0, h=100.5, l=99.5, c=100.0, tf_ms=60_000))

    b4 = [_bar(i, tf_ms=4 * 3600_000) for i in range(8)]
    b1 = [_bar(i, tf_ms=3600_000) for i in range(20)]
    b15 = [_bar(i, tf_ms=15 * 60_000) for i in range(40)]
    bundle = build_tf_bundle(b4, b1, b15, bars_1m)

    setup = NotebookSetup(
        side=LONG,
        msb_1h_index=0,
        msb_1h_ts_close_ms=b1[0].ts_close_ms,
        confirm_15m_index=0,
        confirm_15m_ts_close_ms=b15[0].ts_close_ms,
        range_line=97.5,
        atr_15m_at_confirm=1.0,
        sl_structural=97.0,
        bos_1m_index=14,
        bos_1m_ts_open_ms=bars_1m[14].ts_open_ms,
        local_1m_swing=97.5,
        skipped=None,
    )
    settings = EmaBookSettings(equity_eur=20.0, fee_rate=0.0005, slippage_bps=5.0)
    t0 = bars_1m[0].ts_open_ms
    t1 = bars_1m[-1].ts_open_ms + 60_000
    walk = walk_notebook_stretch_cell(
        bundle,
        [setup],
        risk_frac=0.25,
        r_multiple=None,
        use_tp=False,
        settings=settings,
        trade_start_ms=t0,
        trade_end_ms=t1,
    )
    assert walk["n_entries"] == 1, walk
    assert walk["n_tp_exits"] == 0
    assert walk["exit_mix"]["tp"] == 0
    assert walk["n_msb_exits"] == 0
    assert walk["n_sl_exits"] == 1


def test_t1_same_bar_sl_tp_fail_closed_sl() -> None:
    bars_1m = []
    for i in range(40):
        if i == 15:
            bars_1m.append(_bar(i, o=100.0, h=100.5, l=99.5, c=100.2, tf_ms=60_000))
        elif i == 16:
            bars_1m.append(_bar(i, o=100.0, h=130.0, l=95.0, c=101.0, tf_ms=60_000))
        else:
            bars_1m.append(_bar(i, o=100.0, h=100.5, l=99.5, c=100.0, tf_ms=60_000))

    b4 = [_bar(i, tf_ms=4 * 3600_000) for i in range(8)]
    b1 = [_bar(i, tf_ms=3600_000) for i in range(20)]
    b15 = [_bar(i, tf_ms=15 * 60_000) for i in range(40)]
    bundle = build_tf_bundle(b4, b1, b15, bars_1m)

    setup = NotebookSetup(
        side=LONG,
        msb_1h_index=0,
        msb_1h_ts_close_ms=b1[0].ts_close_ms,
        confirm_15m_index=0,
        confirm_15m_ts_close_ms=b15[0].ts_close_ms,
        range_line=97.5,
        atr_15m_at_confirm=1.0,
        sl_structural=97.0,
        bos_1m_index=14,
        bos_1m_ts_open_ms=bars_1m[14].ts_open_ms,
        local_1m_swing=97.5,
        skipped=None,
    )
    settings = EmaBookSettings(equity_eur=20.0, fee_rate=0.0005, slippage_bps=5.0)
    t0 = bars_1m[0].ts_open_ms
    t1 = bars_1m[-1].ts_open_ms + 60_000
    walk = walk_notebook_stretch_cell(
        bundle,
        [setup],
        risk_frac=0.25,
        r_multiple=4.0,
        use_tp=True,
        settings=settings,
        trade_start_ms=t0,
        trade_end_ms=t1,
    )
    assert walk["n_entries"] == 1, walk
    assert walk["n_sl_exits"] == 1
    assert walk["n_tp_exits"] == 0
    assert walk["n_msb_exits"] == 0


def test_discover_setups_accepts_rvol_gate_override() -> None:
    """T3 hook: discover_setups(rvol_gate=0.8) is callable (synthetic empty-ish)."""
    def series(n: int, tf_ms: int) -> list[Bar]:
        out = []
        for i in range(n):
            h = 110.0 if i % 17 == 8 else 101.0
            l = 90.0 if i % 19 == 9 else 99.0
            out.append(_bar(i, h=h, l=l, c=100.0, v=5.0, tf_ms=tf_ms))
        return out

    b4 = series(40, 4 * 3600_000)
    b1 = series(120, 3600_000)
    b15 = series(200, 15 * 60_000)
    b1m = series(500, 60_000)
    bundle = build_tf_bundle(b4, b1, b15, b1m)
    s_default = discover_setups(bundle, side=LONG)
    s_08 = discover_setups(bundle, side=LONG, rvol_gate=0.8)
    assert isinstance(s_default, list)
    assert isinstance(s_08, list)
    # With lower gate, skip_rvol count should be <= default (more or equal confirms)
    skip_def = sum(1 for s in s_default if s.skipped == "rvol")
    skip_08 = sum(1 for s in s_08 if s.skipped == "rvol")
    assert skip_08 <= skip_def


def test_msb_always_off() -> None:
    def series(n: int, tf_ms: int) -> list[Bar]:
        return [_bar(i, c=100.0, v=5.0, tf_ms=tf_ms) for i in range(n)]

    b4 = series(20, 4 * 3600_000)
    b1 = series(60, 3600_000)
    b15 = series(100, 15 * 60_000)
    b1m = series(200, 60_000)
    bundle = build_tf_bundle(b4, b1, b15, b1m)
    settings = EmaBookSettings(equity_eur=20.0, fee_rate=0.0005, slippage_bps=5.0)
    t0 = b1m[0].ts_open_ms
    t1 = b1m[-1].ts_open_ms + 60_000
    for use_tp, r_mult in ((True, 4.0), (False, None), (True, 3.0)):
        walk = walk_notebook_stretch_cell(
            bundle,
            [],
            risk_frac=0.25,
            r_multiple=r_mult,
            use_tp=use_tp,
            settings=settings,
            trade_start_ms=t0,
            trade_end_ms=t1,
        )
        assert walk["n_msb_exits"] == 0
        assert walk["exit_mix"]["msb_exit"] == 0
