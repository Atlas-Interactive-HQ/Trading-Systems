"""#135 S4 — A DT N20 RVOL>1 ENTRY + ATR trail 2×ATR14 + EMA-flip + ts168.

Replaces fixed SellLine-only SL with ratchet ATR trail (never loosens).
Still 4H EMA21 flip + time-stop 168. NO 1.5R. NO sell-line profit exit.
Paper only. Do not grind N/k/RVOL/ATR mult.
"""

from __future__ import annotations

from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.scalp_135_common import (
    ATR_N,
    ATR_TRAIL_MULT,
    EMA_4H,
    TIME_STOP,
    Scalp135Signals,
)
from atlas.strategy.scalp_dt_rvol_1h_133 import (
    ScalpDtRvol1h133V1,
)

CELL = "A"
SID = "S4"
FAMILY = "dt_n20_k0505_rvol20_gt10_ema21_4h_emaflip_atrtrail2_ts168"
EXIT_MODE = "atr_trail_2x"


def precompute_s4_a(
    bars_1h: Sequence[Bar],
    bars_4h: Sequence[Bar],
) -> Scalp135Signals:
    """Reuse #133 entry precompute; ignore sell_line as fixed SL (trail replaces it)."""
    sig = ScalpDtRvol1h133V1().precompute_signals(bars_1h, bars_4h)
    # sl_ref unused for S4 trail mode (walker seeds trail from atr)
    sl_ref: list[float | None] = [None] * len(bars_1h)
    return Scalp135Signals(
        entry_ok=list(sig.entry_ok),
        regime_flip=list(sig.regime_flip),
        atr=list(sig.atr),
        sl_ref=sl_ref,
    )


__all__ = [
    "ATR_N",
    "ATR_TRAIL_MULT",
    "CELL",
    "EMA_4H",
    "EXIT_MODE",
    "FAMILY",
    "SID",
    "TIME_STOP",
    "precompute_s4_a",
]
