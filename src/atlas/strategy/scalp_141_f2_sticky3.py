"""#141 F2 — E1/D3 entry + seed; exit after 3 consecutive 1D close < EMA21. NO SL.

Entry: 1D close > EMA21 OR FULL seed → next 1H open. Long-only. Max 1.
Exit: only after 3 consecutive closed 1D bars with close < EMA21 → next 1H open.
NO SL. n_time_stop=0. NO shorts. Window-end residual → forced_end (not ts).
"""

from __future__ import annotations

from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.scalp_141_common import (
    EMA_1D,
    EMA_1D_SLOW,
    F2_STICKY_N,
    NO_TIME_STOP,
    TIME_STOP,
    Scalp141Signals,
    entry_ok_with_seed,
    sticky_lt_ema_exit_series,
)

CELL = "F2"
FAMILY = "f2_sticky3"
FAMILY_LABEL = "F2=E1/D3 entry+seed + sticky 3x 1D close<EMA21 exit + NO SL + NO ts"
EXIT_MODE = "no_sl_sticky3_1d_lt_ema21_no_ts"
SL_MODE = "none"
PARENT_SID = "E1"
PARENT_PHASE = 140


def precompute_f2_sticky3(
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
    flip = sticky_lt_ema_exit_series(
        bars_1h, bars_1d, ema_period=EMA_1D, n_consec=F2_STICKY_N
    )
    return Scalp141Signals(
        entry_ok=list(entry_ok),
        regime_flip=list(flip),
        seed_fired=list(seed),
    )


__all__ = [
    "CELL",
    "EMA_1D",
    "EMA_1D_SLOW",
    "EXIT_MODE",
    "F2_STICKY_N",
    "FAMILY",
    "FAMILY_LABEL",
    "NO_TIME_STOP",
    "PARENT_PHASE",
    "PARENT_SID",
    "SL_MODE",
    "TIME_STOP",
    "precompute_f2_sticky3",
]
