"""Supertrend (basic) — ATR trail bands. Research only. not_a_forecast.

Formula (documented for #134 cell F):
  ATR = Wilder ATR(period)
  hl2 = (high + low) / 2
  basic_upper = hl2 + multiplier * ATR
  basic_lower = hl2 - multiplier * ATR
  final_upper trails down: if close[i-1] <= final_upper[i-1] then
      final_upper[i] = min(basic_upper[i], final_upper[i-1]) else basic_upper[i]
  final_lower trails up: if close[i-1] >= final_lower[i-1] then
      final_lower[i] = max(basic_lower[i], final_lower[i-1]) else basic_lower[i]
  Trend: if close > final_upper → long (direction=+1), ST = final_lower
         if close < final_lower → short (direction=-1), ST = final_upper
         else keep prior direction / ST band.
Causal: uses only bars[:i+1]. No lookahead.
"""

from __future__ import annotations

from typing import Sequence

from atlas.paper.types import Bar, q
from atlas.strategy.scalp_dt_rvol_1h_132 import atr_wilder_series

DEFAULT_PERIOD = 10
DEFAULT_MULT = 3.0


def supertrend_series(
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    *,
    period: int = DEFAULT_PERIOD,
    multiplier: float = DEFAULT_MULT,
) -> tuple[list[float | None], list[int | None]]:
    """Return (supertrend_line, direction) where direction is +1 long / -1 short."""
    n = len(closes)
    st: list[float | None] = [None] * n
    direction: list[int | None] = [None] * n
    if period < 1 or n == 0 or multiplier <= 0:
        return st, direction
    atrs = atr_wilder_series(highs, lows, closes, period=period)
    final_upper: list[float | None] = [None] * n
    final_lower: list[float | None] = [None] * n
    for i in range(n):
        atr = atrs[i]
        if atr is None:
            continue
        hl2 = (float(highs[i]) + float(lows[i])) / 2.0
        bu = hl2 + float(multiplier) * float(atr)
        bl = hl2 - float(multiplier) * float(atr)
        if i == 0 or final_upper[i - 1] is None or final_lower[i - 1] is None:
            final_upper[i] = q(bu)
            final_lower[i] = q(bl)
        else:
            prev_fu = float(final_upper[i - 1])
            prev_fl = float(final_lower[i - 1])
            prev_c = float(closes[i - 1])
            if prev_c <= prev_fu:
                final_upper[i] = q(min(bu, prev_fu))
            else:
                final_upper[i] = q(bu)
            if prev_c >= prev_fl:
                final_lower[i] = q(max(bl, prev_fl))
            else:
                final_lower[i] = q(bl)
        c = float(closes[i])
        fu = float(final_upper[i])  # type: ignore[arg-type]
        fl = float(final_lower[i])  # type: ignore[arg-type]
        if c > fu:
            direction[i] = 1
            st[i] = q(fl)
        elif c < fl:
            direction[i] = -1
            st[i] = q(fu)
        else:
            prev_d = direction[i - 1] if i > 0 else None
            if prev_d is None:
                # Seed: treat as long if close >= hl2 else short
                direction[i] = 1 if c >= hl2 else -1
            else:
                direction[i] = int(prev_d)
            st[i] = q(fl if direction[i] == 1 else fu)
    return st, direction


def supertrend_bars(
    bars: Sequence[Bar],
    *,
    period: int = DEFAULT_PERIOD,
    multiplier: float = DEFAULT_MULT,
) -> tuple[list[float | None], list[int | None]]:
    return supertrend_series(
        [float(b.high) for b in bars],
        [float(b.low) for b in bars],
        [float(b.close) for b in bars],
        period=period,
        multiplier=multiplier,
    )


__all__ = [
    "DEFAULT_MULT",
    "DEFAULT_PERIOD",
    "supertrend_bars",
    "supertrend_series",
]
