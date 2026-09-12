"""#139 D2 — always-in 1D EMA21 flip long/short. NO SL.

1D close > EMA21 → long; 1D close < EMA21 → short; fill next 1H open.
Flip-in-place (exit+reverse same bar fill). Max 1 pos. n_time_stop=0.
NO 1.5R. NO ATR trail.
"""

from __future__ import annotations

from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.scalp_139_common import (
    EMA_1D,
    NO_TIME_STOP,
    TIME_STOP,
    Scalp139Signals,
    always_in_side_series_1d_ema21,
)

CELL = "D2"
FAMILY = "d2_alwaysin"
FAMILY_LABEL = "D2=always-in 1D EMA21 flip long/short + NO SL + flip-in-place + NO ts"
EXIT_MODE = "no_sl_alwaysin_1d_ema21_flip_inplace_no_ts"
SL_MODE = "none"
PARENT_SID = "C2"
PARENT_PHASE = 138
ALLOWS_SHORT = True


def precompute_d2_alwaysin(
    bars_1h: Sequence[Bar],
    bars_1d: Sequence[Bar],
) -> Scalp139Signals:
    n = len(bars_1h)
    desired = always_in_side_series_1d_ema21(bars_1h, bars_1d, ema_period=EMA_1D)
    # entry_ok / regime_flip unused by always-in walker (desired_side drives).
    return Scalp139Signals(
        entry_ok=[False] * n,
        regime_flip=[False] * n,
        desired_side=list(desired),
    )


__all__ = [
    "ALLOWS_SHORT",
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
    "precompute_d2_alwaysin",
]
