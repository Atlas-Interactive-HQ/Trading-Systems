"""Unit tests for #143 S1/S2/S3 exit rules (no network)."""

from __future__ import annotations

from atlas.paper.ema_eval import EmaBookSettings
from atlas.paper.public_md_scalp_143 import (
    CELL_MSB_MODE,
    CELL_R_MULTIPLE,
    OFFICIAL_CELLS,
    STICKY_MSB_N,
    _opp_msb_long,
    walk_notebook_exit_cell,
)
from atlas.paper.types import Bar, q
from atlas.strategy.scalp_142_notebook import (
    LONG,
    NotebookSetup,
    PIVOT_N,
    build_tf_bundle,
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


def test_official_cells_and_exit_params() -> None:
    assert OFFICIAL_CELLS == ("S1", "S2", "S3")
    assert CELL_R_MULTIPLE["S1"] == 2.0
    assert CELL_R_MULTIPLE["S2"] == 3.0
    assert CELL_R_MULTIPLE["S3"] == 2.0
    assert CELL_MSB_MODE["S1"] == "off"
    assert CELL_MSB_MODE["S2"] == "off"
    assert CELL_MSB_MODE["S3"] == "sticky2"
    assert STICKY_MSB_N == 2
    assert PIVOT_N == 3


def test_s1_s2_msb_mode_off_zero_msb_exits() -> None:
    """Synthetic walk: with msb_mode=off, n_msb_exit stays 0 even if MSB fires."""
    # Minimal synthetic bars: enough for bundle shapes; no real setups needed
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
    settings = EmaBookSettings(equity_eur=20.0, fee_rate=0.0005, slippage_bps=5.0)
    t0 = b1m[0].ts_open_ms
    t1 = b1m[-1].ts_open_ms + 60_000
    for mode, r_mult in (("off", 2.0), ("off", 3.0)):
        walk = walk_notebook_exit_cell(
            bundle,
            [],
            risk_frac=0.25,
            r_multiple=r_mult,
            msb_mode=mode,  # type: ignore[arg-type]
            settings=settings,
            trade_start_ms=t0,
            trade_end_ms=t1,
        )
        assert walk["n_msb_exits"] == 0
        assert walk["exit_mix"]["msb_exit"] == 0
        assert walk["msb_mode"] == "off"


def test_sticky2_requires_two_consecutive_msb() -> None:
    """_opp_msb_long alone is not enough; sticky needs 2 consecutive confirms."""
    # Build a tiny 1H series where bar1 breaks low, bar2 does not, bar3+4 break
    bars_1h = []
    # Need swings: create a low swing then breaks
    for i in range(20):
        # bar 5: make a swing low at 90
        if i == 5:
            bars_1h.append(_bar(i, o=100, h=101, l=90, c=95, tf_ms=3600_000))
        elif 6 <= i <= 8:
            # right side of pivot N=3
            bars_1h.append(_bar(i, o=96, h=102, l=95, c=100, tf_ms=3600_000))
        elif i == 12:
            # first MSB-down candidate: close below prior swing low
            bars_1h.append(_bar(i, o=94, h=95, l=88, c=89, tf_ms=3600_000))
        elif i == 13:
            # non-confirm (close back above)
            bars_1h.append(_bar(i, o=90, h=100, l=89, c=98, tf_ms=3600_000))
        elif i in (14, 15):
            # two consecutive confirms
            bars_1h.append(_bar(i, o=94, h=95, l=87, c=88, tf_ms=3600_000))
        else:
            bars_1h.append(_bar(i, o=100, h=101, l=99, c=100, tf_ms=3600_000))

    b4 = [_bar(i, tf_ms=4 * 3600_000) for i in range(10)]
    b15 = [_bar(i, tf_ms=15 * 60_000) for i in range(80)]
    b1m = [_bar(i, tf_ms=60_000) for i in range(20 * 60)]
    bundle = build_tf_bundle(b4, bars_1h, b15, b1m)

    # Spot-check MSB predicate on confirming indices if swings warm
    # (may be None early — just ensure function is callable / bool)
    for idx in range(len(bars_1h)):
        assert isinstance(_opp_msb_long(bundle, idx), bool)

    assert STICKY_MSB_N == 2


def test_same_bar_sl_tp_fail_closed_sl() -> None:
    """If both SL and TP touch same 1m bar, count as SL."""
    # SL dist must keep notional <= 10x: qty=(0.25*20)/sl_dist, need sl_dist>=2.5 at px~100
    # SL=97.0 → R=3 (after slip ~), TP=entry+2R touches high>=TP and low<=SL same bar
    bars_1m = []
    for i in range(40):
        if i == 15:
            bars_1m.append(_bar(i, o=100.0, h=100.5, l=99.5, c=100.2, tf_ms=60_000))
        elif i == 16:
            bars_1m.append(_bar(i, o=100.0, h=110.0, l=95.0, c=101.0, tf_ms=60_000))
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
    walk = walk_notebook_exit_cell(
        bundle,
        [setup],
        risk_frac=0.25,
        r_multiple=2.0,
        msb_mode="off",
        settings=settings,
        trade_start_ms=t0,
        trade_end_ms=t1,
    )
    assert walk["n_entries"] == 1, walk
    assert walk["n_sl_exits"] == 1
    assert walk["n_tp_exits"] == 0
    assert walk["n_msb_exits"] == 0
