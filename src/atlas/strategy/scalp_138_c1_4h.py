"""#138 C1 — 4H EMA21 regime-hold. NO scalp channel (no Keltner/Donchian/DT).

flat→long when 4H close > EMA21; exit when 4H close < EMA21 → next 1H open.
SL = entry − 3×ATR14(1H) fixed. Max 1 position. NO time-stop.
NO 1.5R. NO ATR trail.
"""

from __future__ import annotations

from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.scalp_dt_rvol_1h_133 import atr_wilder_1h
from atlas.strategy.scalp_138_common import (
    ATR_N,
    ATR_SL_MULT,
    EMA_4H,
    NO_TIME_STOP,
    TIME_STOP,
    Scalp138Signals,
    regime_flip_series_4h_ema21,
    regime_ok_series_4h_ema21,
)

CELL = "C1"
FAMILY = "c1_4h"
FAMILY_LABEL = "C1=4H EMA21 regime-hold + ATR3 SL + NO ts (no channel)"
EXIT_MODE = "fixed_atr3_sl_4h_ema21_flip_no_ts"
SL_MODE = "atr"
PARENT_SID = "S2"
PARENT_LETTER = "G"
PARENT_PHASE = 135


def precompute_c1_4h(
    bars_1h: Sequence[Bar],
    bars_4h: Sequence[Bar],
    bars_1d: Sequence[Bar],
) -> Scalp138Signals:
    del bars_1d  # C1 does not use 1D
    n = len(bars_1h)
    entry_ok = regime_ok_series_4h_ema21(bars_1h, bars_4h, ema_period=EMA_4H)
    flip_4h = regime_flip_series_4h_ema21(bars_1h, bars_4h, ema_period=EMA_4H)
    atrs = atr_wilder_1h(bars_1h, period=ATR_N)
    # No channel: sl_ref unused (ATR SL at fill).
    sl_ref: list[float | None] = [None] * n
    return Scalp138Signals(
        entry_ok=list(entry_ok),
        regime_flip=list(flip_4h),  # active exit = 4H flip
        regime_flip_4h=list(flip_4h),
        sl_ref=sl_ref,
        atr=atrs,
    )


__all__ = [
    "ATR_N",
    "ATR_SL_MULT",
    "CELL",
    "EMA_4H",
    "EXIT_MODE",
    "FAMILY",
    "FAMILY_LABEL",
    "NO_TIME_STOP",
    "PARENT_LETTER",
    "PARENT_PHASE",
    "PARENT_SID",
    "SL_MODE",
    "TIME_STOP",
    "precompute_c1_4h",
]
