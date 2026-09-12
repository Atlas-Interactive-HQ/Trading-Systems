"""#135 S1 — F Supertrend(10,3) ENTRY + A-style exits (fixed SL / EMA-flip / ts168).

NO 1.5R. NO Supertrend flip exit. NO extra ATR trail.
Paper only. Do not grind ST period/mult.
"""

from __future__ import annotations

from typing import Sequence

from atlas.paper.types import Bar
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
from atlas.strategy.supertrend import DEFAULT_MULT, DEFAULT_PERIOD, supertrend_bars

ST_PERIOD = DEFAULT_PERIOD  # 10
ST_MULT = DEFAULT_MULT  # 3.0
CELL = "F"
SID = "S1"
FAMILY = "supertrend10_3_1h_ema21_4h_emaflip_ts168"
EXIT_MODE = "a_style_fixed_sl"


def precompute_s1_f(
    bars_1h: Sequence[Bar],
    bars_4h: Sequence[Bar],
) -> Scalp135Signals:
    n = len(bars_1h)
    regime = regime_ok_series_4h_ema(bars_1h, bars_4h, ema_period=EMA_4H)
    flip = regime_flip_series_4h_ema(bars_1h, bars_4h, ema_period=EMA_4H)
    atrs = atr_wilder_1h(bars_1h, period=ATR_N)
    st_line, direction = supertrend_bars(bars_1h, period=ST_PERIOD, multiplier=ST_MULT)
    entry_ok = [False] * n
    sl_ref: list[float | None] = [None] * n
    for i in range(n):
        if not bars_1h[i].closed:
            continue
        st = st_line[i]
        sl_ref[i] = float(st) if st is not None else None
        d = direction[i]
        if d is None or i == 0:
            continue
        prev_d = direction[i - 1]
        if prev_d is None:
            continue
        # Flip to long + 4H EMA21 regime
        if int(prev_d) <= 0 and int(d) == 1 and regime[i]:
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
    "SID",
    "ST_MULT",
    "ST_PERIOD",
    "TIME_STOP",
    "precompute_s1_f",
]
