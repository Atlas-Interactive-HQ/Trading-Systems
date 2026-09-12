"""#134 cell C — 1H Donchian(20) close > prior high + 4H EMA21. Paper only."""

from __future__ import annotations

from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.breakout import donchian_prior
from atlas.strategy.scalp_134_common import Batch134Signals
from atlas.strategy.scalp_dt_rvol_1h_132 import atr_wilder_1h, regime_ok_series_4h_ema

LOOKBACK = 20
ATR_N = 14
R = 1.5
TIME_STOP = 24
EMA_4H = 21
CELL = "C"
FAMILY = "donchian20_mid_sl_1h_ema21_4h"


def precompute_c(
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
        if ch is None:
            continue
        prior_high, prior_low = ch
        mid = (float(prior_high) + float(prior_low)) / 2.0
        c = float(bar.close)
        sl_ref[i] = mid
        if regime[i] and c > float(prior_high):
            entry_ok[i] = True
    return Batch134Signals(entry_ok=entry_ok, exit_ok=exit_ok, atr=atrs, sl_ref=sl_ref)


__all__ = [
    "ATR_N",
    "CELL",
    "EMA_4H",
    "FAMILY",
    "LOOKBACK",
    "R",
    "TIME_STOP",
    "precompute_c",
]
