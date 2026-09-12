"""#136 L2 — same ENTRY as #135 S3 / #134 C Donchian(20).

1H close > prior Donchian high AND 4H close > EMA21.
SL = Donchian mid at entry, fixed.
Exits (walker): honor fixed SL · 1D close < EMA21 → next 1H open · ts504.
NO 1.5R. NO 4H EMA flip exit. NO ATR trail. Do not grind Donchian N.
"""

from __future__ import annotations

from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.breakout import donchian_prior
from atlas.strategy.scalp_136_common import (
    ATR_N,
    EMA_1D,
    EMA_4H,
    TIME_STOP,
    Scalp136Signals,
    regime_flip_series_1d_ema21,
    regime_flip_series_4h_ema21,
    regime_ok_series_4h_ema21,
)
from atlas.strategy.scalp_dt_rvol_1h_133 import atr_wilder_1h

LOOKBACK = 20
CELL = "L2"
FAMILY = "l2_donchian"
FAMILY_LABEL = "L2=S3/C Donchian20 entry + 1D EMA21 flip + ts504"
EXIT_MODE = "fixed_sl_1d_ema21_flip_ts504"
PARENT_SID = "S3"
PARENT_LETTER = "C"


def precompute_l2_donchian(
    bars_1h: Sequence[Bar],
    bars_4h: Sequence[Bar],
    bars_1d: Sequence[Bar],
) -> Scalp136Signals:
    n = len(bars_1h)
    regime = regime_ok_series_4h_ema21(bars_1h, bars_4h, ema_period=EMA_4H)
    flip_1d = regime_flip_series_1d_ema21(bars_1h, bars_1d, ema_period=EMA_1D)
    flip_4h = regime_flip_series_4h_ema21(bars_1h, bars_4h, ema_period=EMA_4H)
    atrs = atr_wilder_1h(bars_1h, period=ATR_N)
    entry_ok = [False] * n
    sl_ref: list[float | None] = [None] * n
    for i in range(n):
        bar = bars_1h[i]
        if not bar.closed:
            continue
        hist = bars_1h[: i + 1]
        ch = donchian_prior(hist, LOOKBACK)
        if ch is None:
            continue
        prior_high, prior_low = ch
        mid = (float(prior_high) + float(prior_low)) / 2.0
        c = float(bar.close)
        sl_ref[i] = mid
        if regime[i] and c > float(prior_high):
            entry_ok[i] = True
    return Scalp136Signals(
        entry_ok=entry_ok,
        regime_flip=list(flip_1d),
        regime_flip_4h=list(flip_4h),
        sl_ref=sl_ref,
        atr=atrs,
    )


__all__ = [
    "ATR_N",
    "CELL",
    "EMA_1D",
    "EMA_4H",
    "EXIT_MODE",
    "FAMILY",
    "FAMILY_LABEL",
    "LOOKBACK",
    "PARENT_LETTER",
    "PARENT_SID",
    "TIME_STOP",
    "precompute_l2_donchian",
]
