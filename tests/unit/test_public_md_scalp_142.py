"""Unit smoke for #142 notebook stack (no network)."""

from __future__ import annotations

from atlas.paper.types import Bar
from atlas.strategy.scalp_142_notebook import (
    PIVOT_N,
    RVOL_GATE,
    atr_from_bars,
    build_tf_bundle,
)


def _bar(i: int, *, o=100.0, h=101.0, l=99.0, c=100.0, v=1.0, tf_ms=60_000) -> Bar:
    t0 = 1_590_969_600_000 + i * tf_ms
    return Bar(
        symbol="BTC-USDT",
        ts_open_ms=t0,
        ts_close_ms=t0 + tf_ms - 1,
        open=o,
        high=h,
        low=l,
        close=c,
        volume=v,
        closed=True,
    )


def test_atr_warm_and_rvol_gate_constant() -> None:
    bars = [_bar(i, h=100 + (i % 5), l=100 - (i % 5), c=100.0, v=10.0 + i) for i in range(40)]
    atr = atr_from_bars(bars, period=14)
    assert atr[13] is not None
    assert atr[12] is None
    assert RVOL_GATE == 1.0
    assert PIVOT_N == 3


def test_build_tf_bundle_shapes() -> None:
    def series(n: int, tf_ms: int) -> list[Bar]:
        out = []
        for i in range(n):
            h = 110.0 if i % 17 == 8 else 101.0
            l = 90.0 if i % 19 == 9 else 99.0
            out.append(_bar(i, h=h, l=l, c=100.0, v=5.0, tf_ms=tf_ms))
        return out

    b4 = series(80, 4 * 3600_000)
    b1 = series(200, 3600_000)
    b15 = series(400, 15 * 60_000)
    b1m = series(2000, 60_000)
    bundle = build_tf_bundle(b4, b1, b15, b1m)
    assert len(bundle.atr_4h) == len(b4)
    assert len(bundle.asof_1m_high) == len(b1m)
    assert len(bundle.rvol_15m) == len(b15)
