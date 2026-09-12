"""#137 N1 — same ENTRY as #136 L2 / #135 S3 Donchian(20).

1H close > prior Donchian high AND 4H close > EMA21.
SL = Donchian mid at entry, fixed.
Exits (walker): honor fixed SL · 1D close < EMA21 → next 1H open · NO time-stop.
NO 1.5R. NO 4H EMA flip exit. NO ATR trail. Do not grind Donchian N.
"""

from __future__ import annotations

from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.scalp_136_l2_donchian import LOOKBACK, precompute_l2_donchian
from atlas.strategy.scalp_137_common import (
    ATR_N,
    EMA_1D,
    EMA_4H,
    NO_TIME_STOP,
    TIME_STOP,
    Scalp137Signals,
)

CELL = "N1"
FAMILY = "n1_donchian"
FAMILY_LABEL = "N1=L2/S3 Donchian20 entry + 1D EMA21 flip + NO ts"
EXIT_MODE = "fixed_sl_1d_ema21_flip_no_ts"
PARENT_SID = "L2"
PARENT_LETTER = "L2"
PARENT_PHASE = 136


def precompute_n1_donchian(
    bars_1h: Sequence[Bar],
    bars_4h: Sequence[Bar],
    bars_1d: Sequence[Bar],
) -> Scalp137Signals:
    """Reuse #136 L2 Donchian precompute (entry + 1D flip identical)."""
    return precompute_l2_donchian(bars_1h, bars_4h, bars_1d)


__all__ = [
    "ATR_N",
    "CELL",
    "EMA_1D",
    "EMA_4H",
    "EXIT_MODE",
    "FAMILY",
    "FAMILY_LABEL",
    "LOOKBACK",
    "NO_TIME_STOP",
    "PARENT_LETTER",
    "PARENT_PHASE",
    "PARENT_SID",
    "TIME_STOP",
    "precompute_n1_donchian",
]
