"""Causal EMA and Wilder ATR for Atlas Cycle v1.

EMA: alpha = 2/(n+1), seeded with the SMA of the first n closes.
ATR: Wilder, seeded with the SMA of the first n true ranges.

Both delegate to the existing paper helpers so the rounding matches the rest
of the repo (8 dp half-up via ``q``). Values at index i depend only on bars
``0..i``.
"""

from __future__ import annotations

from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.ema_trend import ema_series
from atlas.strategy.scalp_dt_rvol_15m_130 import atr_wilder_series

BAR_15_MS = 15 * 60 * 1000
BAR_1H_MS = 60 * 60 * 1000
BAR_4H_MS = 4 * 60 * 60 * 1000


def ema_at(closes: Sequence[float], period: int) -> list[float | None]:
    return ema_series(closes, period)


def atr14(bars: Sequence[Bar], period: int = 14) -> list[float | None]:
    return atr_wilder_series(
        [float(b.high) for b in bars],
        [float(b.low) for b in bars],
        [float(b.close) for b in bars],
        period=period,
    )


def resample_fixed(bars_15m: Sequence[Bar], span_ms: int, width: int) -> list[Bar]:
    """Complete UTC-aligned buckets only. Incomplete edges are dropped.

    ``width`` is the number of 15m bars in the bucket (4 for 1H, 16 for 4H).
    A bucket is emitted only when it contains ``width`` bars and the first
    open sits on the bucket boundary. No partial bar is invented.
    """
    if width < 2 or span_ms != width * BAR_15_MS:
        raise ValueError("span must equal width * 15m")
    buckets: dict[int, list[Bar]] = {}
    for bar in bars_15m:
        if not bar.closed:
            continue
        key = (bar.ts_open_ms // span_ms) * span_ms
        buckets.setdefault(key, []).append(bar)
    out: list[Bar] = []
    for key in sorted(buckets):
        rows = sorted(buckets[key], key=lambda item: item.ts_open_ms)
        if len(rows) != width or rows[0].ts_open_ms != key:
            continue
        expected = key
        contiguous = True
        for row in rows:
            if row.ts_open_ms != expected:
                contiguous = False
                break
            expected += BAR_15_MS
        if not contiguous:
            continue
        out.append(
            Bar(
                rows[0].symbol,
                key,
                key + span_ms,
                rows[0].open,
                max(row.high for row in rows),
                min(row.low for row in rows),
                rows[-1].close,
                sum(row.volume for row in rows),
                True,
                "resample_15m_utc",
            )
        )
    return out


def last_closed_index(bars: Sequence[Bar], ts_close_ms: int) -> int | None:
    """Rightmost bar whose close is <= ``ts_close_ms``. None if none qualify."""
    lo = 0
    hi = len(bars) - 1
    found: int | None = None
    while lo <= hi:
        mid = (lo + hi) // 2
        if bars[mid].ts_close_ms <= ts_close_ms:
            found = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return found
