"""#138 C3 — same ENTRY as #137 N2 / #135 S2 Keltner; slower 1D EMA50 flip exit.

1H close > Keltner upper (EMA20 + 1.5×ATR20) AND 4H close > EMA21.
SL = Keltner mid (EMA20) at entry, fixed.
Exit = SL OR 1D close < EMA50 → next 1H open. NO time-stop.
NO 1.5R. NO ATR trail. Slower than EMA21 flip.
"""

from __future__ import annotations

from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.keltner import DEFAULT_MULT, DEFAULT_PERIOD, keltner_bars
from atlas.strategy.scalp_dt_rvol_1h_133 import atr_wilder_1h
from atlas.strategy.scalp_138_common import (
    ATR_N,
    EMA_1D_SLOW,
    EMA_4H,
    NO_TIME_STOP,
    TIME_STOP,
    Scalp138Signals,
    regime_flip_series_1d_ema,
    regime_flip_series_4h_ema21,
    regime_ok_series_4h_ema21,
)

KC_PERIOD = DEFAULT_PERIOD  # 20
KC_MULT = DEFAULT_MULT  # 1.5
CELL = "C3"
FAMILY = "c3_keltner_ema50"
FAMILY_LABEL = "C3=N2/S2 Keltner(20,1.5) entry + 1D EMA50 flip + NO ts"
EXIT_MODE = "fixed_sl_1d_ema50_flip_no_ts"
SL_MODE = "sl_ref"
PARENT_SID = "N2"
PARENT_LETTER = "N2"
PARENT_PHASE = 137


def precompute_c3_keltner_ema50(
    bars_1h: Sequence[Bar],
    bars_4h: Sequence[Bar],
    bars_1d: Sequence[Bar],
) -> Scalp138Signals:
    n = len(bars_1h)
    regime = regime_ok_series_4h_ema21(bars_1h, bars_4h, ema_period=EMA_4H)
    flip_1d_50 = regime_flip_series_1d_ema(
        bars_1h, bars_1d, ema_period=EMA_1D_SLOW
    )
    flip_4h = regime_flip_series_4h_ema21(bars_1h, bars_4h, ema_period=EMA_4H)
    atrs = atr_wilder_1h(bars_1h, period=ATR_N)
    mid, upper, _lower = keltner_bars(bars_1h, period=KC_PERIOD, multiplier=KC_MULT)
    entry_ok = [False] * n
    sl_ref: list[float | None] = [None] * n
    for i in range(n):
        if not bars_1h[i].closed:
            continue
        m, u = mid[i], upper[i]
        if m is None or u is None:
            continue
        sl_ref[i] = float(m)
        c = float(bars_1h[i].close)
        if regime[i] and c > float(u):
            entry_ok[i] = True
    return Scalp138Signals(
        entry_ok=entry_ok,
        regime_flip=list(flip_1d_50),  # active exit = 1D EMA50 flip
        regime_flip_4h=list(flip_4h),  # honesty only — walker ignores for C3
        sl_ref=sl_ref,
        atr=atrs,
    )


__all__ = [
    "ATR_N",
    "CELL",
    "EMA_1D_SLOW",
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
    "SL_MODE",
    "TIME_STOP",
    "precompute_c3_keltner_ema50",
]
