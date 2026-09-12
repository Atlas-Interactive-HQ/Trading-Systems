"""#134 cell G — 1H Keltner(20, 1.5 ATR) close > upper + 4H EMA21. Paper only."""

from __future__ import annotations

from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.keltner import DEFAULT_MULT, DEFAULT_PERIOD, keltner_bars
from atlas.strategy.scalp_134_common import Batch134Signals
from atlas.strategy.scalp_dt_rvol_1h_132 import atr_wilder_1h, regime_ok_series_4h_ema

KC_PERIOD = DEFAULT_PERIOD  # 20
KC_MULT = DEFAULT_MULT  # 1.5
ATR_N = 14
R = 1.5
TIME_STOP = 24
EMA_4H = 21
CELL = "G"
FAMILY = "keltner20_15_1h_ema21_4h"


def precompute_g(
    bars_1h: Sequence[Bar],
    bars_4h: Sequence[Bar],
) -> Batch134Signals:
    n = len(bars_1h)
    regime = regime_ok_series_4h_ema(bars_1h, bars_4h, ema_period=EMA_4H)
    atrs = atr_wilder_1h(bars_1h, period=ATR_N)
    mid, upper, _lower = keltner_bars(bars_1h, period=KC_PERIOD, multiplier=KC_MULT)
    entry_ok = [False] * n
    exit_ok = [False] * n
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
    return Batch134Signals(entry_ok=entry_ok, exit_ok=exit_ok, atr=atrs, sl_ref=sl_ref)


__all__ = [
    "ATR_N",
    "CELL",
    "EMA_4H",
    "FAMILY",
    "KC_MULT",
    "KC_PERIOD",
    "R",
    "TIME_STOP",
    "precompute_g",
]
