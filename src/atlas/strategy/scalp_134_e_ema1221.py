"""#134 cell E — 1H EMA12/21 cross up + 4H EMA21. Paper only."""

from __future__ import annotations

from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.ema_trend import ema_series
from atlas.strategy.scalp_134_common import Batch134Signals
from atlas.strategy.scalp_dt_rvol_1h_132 import atr_wilder_1h, regime_ok_series_4h_ema

FAST = 12
SLOW = 21
ATR_N = 14
ATR_SL_MULT = 1.5
TIME_STOP = 48
EMA_4H = 21
CELL = "E"
FAMILY = "ema12_21_cross_1h_ema21_4h"


def precompute_e(
    bars_1h: Sequence[Bar],
    bars_4h: Sequence[Bar],
) -> Batch134Signals:
    n = len(bars_1h)
    regime = regime_ok_series_4h_ema(bars_1h, bars_4h, ema_period=EMA_4H)
    atrs = atr_wilder_1h(bars_1h, period=ATR_N)
    closes = [float(b.close) for b in bars_1h]
    fast = ema_series(closes, FAST)
    slow = ema_series(closes, SLOW)
    entry_ok = [False] * n
    exit_ok = [False] * n
    sl_ref: list[float | None] = [None] * n
    for i in range(n):
        if not bars_1h[i].closed:
            continue
        f, s = fast[i], slow[i]
        if f is None or s is None:
            continue
        if i == 0:
            continue
        pf, ps = fast[i - 1], slow[i - 1]
        if pf is None or ps is None:
            continue
        # Cross up: prev fast <= slow, curr fast > slow
        if float(pf) <= float(ps) and float(f) > float(s) and regime[i]:
            entry_ok[i] = True
        # Exit cross down: curr fast < slow
        if float(f) < float(s):
            exit_ok[i] = True
    return Batch134Signals(entry_ok=entry_ok, exit_ok=exit_ok, atr=atrs, sl_ref=sl_ref)


__all__ = [
    "ATR_N",
    "ATR_SL_MULT",
    "CELL",
    "EMA_4H",
    "FAMILY",
    "FAST",
    "SLOW",
    "TIME_STOP",
    "precompute_e",
]
