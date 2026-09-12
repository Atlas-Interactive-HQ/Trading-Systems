"""#140 E3 — C2 entry (1D close > EMA21); exit EMA50∧EMA100. NO SL.

Entry: 1D close > EMA21 → next 1H open. Long-only. Max 1 pos.
Exit: 1D close < EMA50 AND 1D close < EMA100 → next 1H open.
NO SL. n_time_stop=0. NO 1.5R. NO ATR trail. NO shorts.
If EMA100 still cold at FULL start, entries stay off until warm (fail closed).
"""

from __future__ import annotations

from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.scalp_140_common import (
    EMA_1D,
    EMA_1D_SLOW,
    EMA_1D_XSlow,
    NO_TIME_STOP,
    TIME_STOP,
    Scalp140Signals,
    dual_ema_exit_series,
    regime_ok_series_1d_ema,
)

CELL = "E3"
FAMILY = "e3_ema50_100"
FAMILY_LABEL = "E3=EMA21 entry + dual EMA50+EMA100 exit + NO SL + NO ts"
EXIT_MODE = "no_sl_1d_ema50_and_ema100_flip_no_ts"
SL_MODE = "none"
PARENT_SID = "D3"
PARENT_PHASE = 139


def precompute_e3_ema50_100(
    bars_1h: Sequence[Bar],
    bars_1d: Sequence[Bar],
) -> Scalp140Signals:
    n = len(bars_1h)
    entry_ok = regime_ok_series_1d_ema(bars_1h, bars_1d, ema_period=EMA_1D)
    flip = dual_ema_exit_series(
        bars_1h, bars_1d, ema_fast=EMA_1D_SLOW, ema_slow=EMA_1D_XSlow
    )
    return Scalp140Signals(
        entry_ok=list(entry_ok),
        regime_flip=list(flip),
        seed_fired=[False] * n,
    )


__all__ = [
    "CELL",
    "EMA_1D",
    "EMA_1D_SLOW",
    "EMA_1D_XSlow",
    "EXIT_MODE",
    "FAMILY",
    "FAMILY_LABEL",
    "NO_TIME_STOP",
    "PARENT_PHASE",
    "PARENT_SID",
    "SL_MODE",
    "TIME_STOP",
    "precompute_e3_ema50_100",
]
