"""#139 D3 — C2 long entry; exit only when 1D close < EMA21 AND < EMA50. NO SL.

Entry: 1D close > EMA21 → next 1H open. Long-only. Max 1 pos.
Exit: 1D close < EMA21 AND 1D close < EMA50 → next 1H open.
NO SL. n_time_stop=0. NO 1.5R. NO ATR trail.
"""

from __future__ import annotations

from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.scalp_139_common import (
    EMA_1D,
    EMA_1D_SLOW,
    FLAT,
    NO_TIME_STOP,
    TIME_STOP,
    Scalp139Signals,
    dual_ema_exit_series,
    regime_ok_series_1d_ema,
)

CELL = "D3"
FAMILY = "d3_dual_ema"
FAMILY_LABEL = "D3=C2 long entry + dual EMA21+EMA50 exit + NO SL + NO ts"
EXIT_MODE = "no_sl_1d_ema21_and_ema50_flip_no_ts"
SL_MODE = "none"
PARENT_SID = "C2"
PARENT_PHASE = 138


def precompute_d3_dual_ema(
    bars_1h: Sequence[Bar],
    bars_1d: Sequence[Bar],
) -> Scalp139Signals:
    n = len(bars_1h)
    entry_ok = regime_ok_series_1d_ema(bars_1h, bars_1d, ema_period=EMA_1D)
    flip = dual_ema_exit_series(
        bars_1h, bars_1d, ema_fast=EMA_1D, ema_slow=EMA_1D_SLOW
    )
    return Scalp139Signals(
        entry_ok=list(entry_ok),
        regime_flip=list(flip),
        desired_side=[FLAT] * n,
    )


__all__ = [
    "CELL",
    "EMA_1D",
    "EMA_1D_SLOW",
    "EXIT_MODE",
    "FAMILY",
    "FAMILY_LABEL",
    "NO_TIME_STOP",
    "PARENT_PHASE",
    "PARENT_SID",
    "SL_MODE",
    "TIME_STOP",
    "precompute_d3_dual_ema",
]
