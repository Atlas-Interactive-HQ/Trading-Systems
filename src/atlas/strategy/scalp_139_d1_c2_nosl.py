"""#139 D1 — same as #138 C2 long-only, NO SL (isolate ATR3 drag).

flat→long on 1D close > EMA21; exit on 1D close < EMA21 → next 1H open.
NO SL. Max 1 pos. Long-only. n_time_stop=0.
NO 1.5R. NO ATR trail.
"""

from __future__ import annotations

from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.scalp_139_common import (
    EMA_1D,
    FLAT,
    NO_TIME_STOP,
    TIME_STOP,
    Scalp139Signals,
    regime_flip_series_1d_ema,
    regime_ok_series_1d_ema,
)

CELL = "D1"
FAMILY = "d1_c2_nosl"
FAMILY_LABEL = "D1=C2 #138 long-only 1D EMA21 hold + NO SL + NO ts"
EXIT_MODE = "no_sl_1d_ema21_flip_no_ts"
SL_MODE = "none"
PARENT_SID = "C2"
PARENT_PHASE = 138


def precompute_d1_c2_nosl(
    bars_1h: Sequence[Bar],
    bars_1d: Sequence[Bar],
) -> Scalp139Signals:
    n = len(bars_1h)
    entry_ok = regime_ok_series_1d_ema(bars_1h, bars_1d, ema_period=EMA_1D)
    flip = regime_flip_series_1d_ema(bars_1h, bars_1d, ema_period=EMA_1D)
    return Scalp139Signals(
        entry_ok=list(entry_ok),
        regime_flip=list(flip),
        desired_side=[FLAT] * n,  # unused for D1
    )


__all__ = [
    "CELL",
    "EMA_1D",
    "EXIT_MODE",
    "FAMILY",
    "FAMILY_LABEL",
    "NO_TIME_STOP",
    "PARENT_PHASE",
    "PARENT_SID",
    "SL_MODE",
    "TIME_STOP",
    "precompute_d1_c2_nosl",
]
