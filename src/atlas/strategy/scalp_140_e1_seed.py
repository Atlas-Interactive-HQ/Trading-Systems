"""#140 E1 — D3 entry + FULL-window seed; dual EMA21∧EMA50 exit. NO SL.

Entry: 1D close > EMA21 → next 1H open, PLUS seed: if the first FULL-window
1D bar already has close > EMA21, enter next 1H open (don't wait for a fresh
cross). Long-only. Max 1 pos.
Exit: 1D close < EMA21 AND 1D close < EMA50 → next 1H open.
NO SL. n_time_stop=0. NO 1.5R. NO ATR trail. NO shorts.
"""

from __future__ import annotations

from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.scalp_140_common import (
    EMA_1D,
    EMA_1D_SLOW,
    NO_TIME_STOP,
    TIME_STOP,
    Scalp140Signals,
    dual_ema_exit_series,
    entry_ok_with_seed,
)

CELL = "E1"
FAMILY = "e1_seed"
FAMILY_LABEL = "E1=D3 entry + FULL seed + dual EMA21+EMA50 exit + NO SL + NO ts"
EXIT_MODE = "no_sl_1d_ema21_and_ema50_flip_no_ts"
SL_MODE = "none"
PARENT_SID = "D3"
PARENT_PHASE = 139


def precompute_e1_seed(
    bars_1h: Sequence[Bar],
    bars_1d: Sequence[Bar],
    *,
    full_start_ms: int,
    full_end_ms: int,
) -> Scalp140Signals:
    entry_ok, seed = entry_ok_with_seed(
        bars_1h,
        bars_1d,
        ema_period=EMA_1D,
        full_start_ms=full_start_ms,
        full_end_ms=full_end_ms,
    )
    flip = dual_ema_exit_series(
        bars_1h, bars_1d, ema_fast=EMA_1D, ema_slow=EMA_1D_SLOW
    )
    return Scalp140Signals(
        entry_ok=list(entry_ok),
        regime_flip=list(flip),
        seed_fired=list(seed),
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
    "precompute_e1_seed",
]
