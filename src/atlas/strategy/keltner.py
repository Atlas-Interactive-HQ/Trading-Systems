"""Keltner Channel — EMA mid ± mult * Wilder ATR. Research only. not_a_forecast.

Formula (documented for #134 cell G):
  mid = EMA(period) of close
  ATR = Wilder ATR(period)
  upper = mid + multiplier * ATR
  lower = mid - multiplier * ATR
Causal. No lookahead.
"""

from __future__ import annotations

from typing import Sequence

from atlas.paper.types import Bar, q
from atlas.strategy.ema_trend import ema_series
from atlas.strategy.scalp_dt_rvol_1h_132 import atr_wilder_series

DEFAULT_PERIOD = 20
DEFAULT_MULT = 1.5


def keltner_series(
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    *,
    period: int = DEFAULT_PERIOD,
    multiplier: float = DEFAULT_MULT,
) -> tuple[list[float | None], list[float | None], list[float | None]]:
    """Return (mid, upper, lower)."""
    n = len(closes)
    mid_out: list[float | None] = [None] * n
    up_out: list[float | None] = [None] * n
    lo_out: list[float | None] = [None] * n
    if period < 1 or n == 0 or multiplier <= 0:
        return mid_out, up_out, lo_out
    mids = ema_series(closes, period)
    atrs = atr_wilder_series(highs, lows, closes, period=period)
    for i in range(n):
        m, a = mids[i], atrs[i]
        if m is None or a is None:
            continue
        mid_out[i] = q(float(m))
        up_out[i] = q(float(m) + float(multiplier) * float(a))
        lo_out[i] = q(float(m) - float(multiplier) * float(a))
    return mid_out, up_out, lo_out


def keltner_bars(
    bars: Sequence[Bar],
    *,
    period: int = DEFAULT_PERIOD,
    multiplier: float = DEFAULT_MULT,
) -> tuple[list[float | None], list[float | None], list[float | None]]:
    return keltner_series(
        [float(b.high) for b in bars],
        [float(b.low) for b in bars],
        [float(b.close) for b in bars],
        period=period,
        multiplier=multiplier,
    )


__all__ = [
    "DEFAULT_MULT",
    "DEFAULT_PERIOD",
    "keltner_bars",
    "keltner_series",
]
