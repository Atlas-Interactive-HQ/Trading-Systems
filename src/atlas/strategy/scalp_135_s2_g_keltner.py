"""#135 S2 — G Keltner(20, 1.5 ATR) ENTRY + A-style exits (fixed SL / EMA-flip / ts168).

NO 1.5R TP. NO extra ATR trail. Paper only. Do not grind KC params.
"""

from __future__ import annotations

from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.keltner import DEFAULT_MULT, DEFAULT_PERIOD, keltner_bars
from atlas.strategy.scalp_135_common import (
    ATR_N,
    EMA_4H,
    TIME_STOP,
    Scalp135Signals,
)
from atlas.strategy.scalp_dt_rvol_1h_133 import (
    atr_wilder_1h,
    regime_flip_series_4h_ema,
    regime_ok_series_4h_ema,
)

KC_PERIOD = DEFAULT_PERIOD  # 20
KC_MULT = DEFAULT_MULT  # 1.5
CELL = "G"
SID = "S2"
FAMILY = "keltner20_15_1h_ema21_4h_emaflip_ts168"
EXIT_MODE = "a_style_fixed_sl"


def precompute_s2_g(
    bars_1h: Sequence[Bar],
    bars_4h: Sequence[Bar],
) -> Scalp135Signals:
    n = len(bars_1h)
    regime = regime_ok_series_4h_ema(bars_1h, bars_4h, ema_period=EMA_4H)
    flip = regime_flip_series_4h_ema(bars_1h, bars_4h, ema_period=EMA_4H)
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
    return Scalp135Signals(
        entry_ok=entry_ok,
        regime_flip=list(flip),
        atr=atrs,
        sl_ref=sl_ref,
    )


__all__ = [
    "ATR_N",
    "CELL",
    "EMA_4H",
    "EXIT_MODE",
    "FAMILY",
    "KC_MULT",
    "KC_PERIOD",
    "SID",
    "TIME_STOP",
    "precompute_s2_g",
]
