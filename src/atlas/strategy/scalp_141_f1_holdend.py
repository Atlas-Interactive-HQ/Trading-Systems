"""#141 F1 — E1/D3 entry + seed; hold-to-end; NO mid-window regime exit. NO SL.

Entry: 1D close > EMA21 OR FULL seed → next 1H open. Long-only. Max 1.
Exit: none mid-window; forced_end at FULL/SUB window end only (not time-stop).
NO SL. n_time_stop=0. NO shorts.
"""

from __future__ import annotations

from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.scalp_141_common import (
    EMA_1D,
    EMA_1D_SLOW,
    NO_TIME_STOP,
    TIME_STOP,
    Scalp141Signals,
    entry_ok_with_seed,
)

CELL = "F1"
FAMILY = "f1_holdend"
FAMILY_LABEL = "F1=E1/D3 entry+seed + hold-to-end forced_end + NO SL + NO ts"
EXIT_MODE = "no_sl_hold_to_end_forced_end_no_ts"
SL_MODE = "none"
PARENT_SID = "E1"
PARENT_PHASE = 140


def precompute_f1_holdend(
    bars_1h: Sequence[Bar],
    bars_1d: Sequence[Bar],
    *,
    full_start_ms: int,
    full_end_ms: int,
) -> Scalp141Signals:
    entry_ok, seed = entry_ok_with_seed(
        bars_1h,
        bars_1d,
        ema_period=EMA_1D,
        full_start_ms=full_start_ms,
        full_end_ms=full_end_ms,
    )
    n = len(bars_1h)
    return Scalp141Signals(
        entry_ok=list(entry_ok),
        regime_flip=[False] * n,  # no mid-window regime exit
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
    "precompute_f1_holdend",
]
