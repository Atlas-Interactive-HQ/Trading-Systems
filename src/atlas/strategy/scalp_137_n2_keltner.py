"""#137 N2 — same ENTRY as #136 L1 / #135 S2 Keltner(20, 1.5 ATR).

1H close > Keltner upper (EMA20 + 1.5×ATR20) AND 4H close > EMA21.
SL = Keltner mid (EMA20) at entry, fixed.
Exits (walker): honor fixed SL · 1D close < EMA21 → next 1H open · NO time-stop.
NO 1.5R. NO 4H EMA flip exit. NO ATR trail. Do not grind KC params.
"""

from __future__ import annotations

from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.scalp_136_l1_keltner import KC_MULT, KC_PERIOD, precompute_l1_keltner
from atlas.strategy.scalp_137_common import (
    ATR_N,
    EMA_1D,
    EMA_4H,
    NO_TIME_STOP,
    TIME_STOP,
    Scalp137Signals,
)

CELL = "N2"
FAMILY = "n2_keltner"
FAMILY_LABEL = "N2=L1/S2 Keltner(20,1.5) entry + 1D EMA21 flip + NO ts"
EXIT_MODE = "fixed_sl_1d_ema21_flip_no_ts"
PARENT_SID = "S2"
PARENT_LETTER = "G"
PARENT_PHASE = 135


def precompute_n2_keltner(
    bars_1h: Sequence[Bar],
    bars_4h: Sequence[Bar],
    bars_1d: Sequence[Bar],
) -> Scalp137Signals:
    """Reuse #136 L1 Keltner precompute (entry + 1D flip identical)."""
    return precompute_l1_keltner(bars_1h, bars_4h, bars_1d)


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
    "NO_TIME_STOP",
    "PARENT_LETTER",
    "PARENT_PHASE",
    "PARENT_SID",
    "TIME_STOP",
    "precompute_n2_keltner",
]
