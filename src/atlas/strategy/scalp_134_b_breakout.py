"""#134 cell B — 1H Breakout lookback 16 + ATR quiet + 4H EMA21. Paper only."""

from __future__ import annotations

from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.breakout import donchian_prior
from atlas.strategy.scalp_134_common import Batch134Signals
from atlas.strategy.scalp_dt_rvol_1h_132 import atr_wilder_1h, regime_ok_series_4h_ema

LOOKBACK = 16
ATR_N = 14
MIN_ATR_FRAC = 0.001  # ATR14/close >= 0.001 (existing 121 quiet)
ATR_SL_MULT = 1.5
R = 1.5
TIME_STOP = 24
EMA_4H = 21
CELL = "B"
FAMILY = "breakout16_atr_quiet_1h_ema21_4h"


def precompute_b(
    bars_1h: Sequence[Bar],
    bars_4h: Sequence[Bar],
) -> Batch134Signals:
    n = len(bars_1h)
    regime = regime_ok_series_4h_ema(bars_1h, bars_4h, ema_period=EMA_4H)
    atrs = atr_wilder_1h(bars_1h, period=ATR_N)
    entry_ok = [False] * n
    exit_ok = [False] * n
    sl_ref: list[float | None] = [None] * n
    for i in range(n):
        bar = bars_1h[i]
        if not bar.closed:
            continue
        hist = bars_1h[: i + 1]
        ch = donchian_prior(hist, LOOKBACK)
        atr = atrs[i]
        if ch is None or atr is None or float(atr) <= 0:
            continue
        upper, _lower = ch
        c = float(bar.close)
        if c <= 0:
            continue
        if float(atr) / c < MIN_ATR_FRAC:
            continue  # quiet / ranging — no entry
        if regime[i] and c > float(upper):
            entry_ok[i] = True
            sl_ref[i] = c - ATR_SL_MULT * float(atr)  # informational; walker uses ATR
    return Batch134Signals(entry_ok=entry_ok, exit_ok=exit_ok, atr=atrs, sl_ref=sl_ref)


__all__ = [
    "ATR_N",
    "ATR_SL_MULT",
    "CELL",
    "EMA_4H",
    "FAMILY",
    "LOOKBACK",
    "MIN_ATR_FRAC",
    "R",
    "TIME_STOP",
    "precompute_b",
]
