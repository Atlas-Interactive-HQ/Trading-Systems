"""#136 L1 — same ENTRY as #135 S2 / #134 G Keltner(20, 1.5 ATR).

1H close > Keltner upper (EMA20 + 1.5×ATR20) AND 4H close > EMA21.
SL = Keltner mid (EMA20) at entry, fixed.
Exits (walker): honor fixed SL · 1D close < EMA21 → next 1H open · ts504.
NO 1.5R. NO 4H EMA flip exit. NO ATR trail. Do not grind KC params.
"""

from __future__ import annotations

from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.keltner import DEFAULT_MULT, DEFAULT_PERIOD, keltner_bars
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

KC_PERIOD = DEFAULT_PERIOD  # 20
KC_MULT = DEFAULT_MULT  # 1.5
CELL = "L1"
FAMILY = "l1_keltner"
FAMILY_LABEL = "L1=S2/G Keltner(20,1.5) entry + 1D EMA21 flip + ts504"
EXIT_MODE = "fixed_sl_1d_ema21_flip_ts504"
PARENT_SID = "S2"
PARENT_LETTER = "G"


def precompute_l1_keltner(
    bars_1h: Sequence[Bar],
    bars_4h: Sequence[Bar],
    bars_1d: Sequence[Bar],
) -> Scalp136Signals:
    n = len(bars_1h)
    regime = regime_ok_series_4h_ema21(bars_1h, bars_4h, ema_period=EMA_4H)
    flip_1d = regime_flip_series_1d_ema21(bars_1h, bars_1d, ema_period=EMA_1D)
    flip_4h = regime_flip_series_4h_ema21(bars_1h, bars_4h, ema_period=EMA_4H)
    atrs = atr_wilder_1h(bars_1h, period=ATR_N)
    mid, upper, _lower = keltner_bars(bars_1h, period=KC_PERIOD, multiplier=KC_MULT)
    entry_ok = [False] * n
    sl_ref: list[float | None] = [None] * n
    for i in range(n):
        if not bars_1h[i].closed:
            continue
        m, u = mid[i], upper[i]
        if m is None or u is None:
            continue
        sl_ref[i] = float(m)
        c = float(bars_1h[i].close)
        if regime[i] and c > float(u):
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
    "KC_MULT",
    "KC_PERIOD",
    "PARENT_LETTER",
    "PARENT_SID",
    "TIME_STOP",
    "precompute_l1_keltner",
]
