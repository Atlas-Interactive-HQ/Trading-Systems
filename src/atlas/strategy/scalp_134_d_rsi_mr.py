"""#134 cell D — 1H RSI14 MR cross-up 30, exit RSI≥55 + 4H EMA21. Paper only."""

from __future__ import annotations

from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.mid_doge_rsi_mr import rsi_wilder
from atlas.strategy.scalp_134_common import Batch134Signals
from atlas.strategy.scalp_dt_rvol_1h_132 import atr_wilder_1h, regime_ok_series_4h_ema

RSI_PERIOD = 14
ENTRY_RSI = 30.0  # prev < 30, close RSI >= 30
EXIT_RSI = 55.0
ATR_N = 14
ATR_SL_MULT = 1.5
TIME_STOP = 24
EMA_4H = 21
CELL = "D"
FAMILY = "rsi14_mr_x30_exit55_1h_ema21_4h"


def precompute_d(
    bars_1h: Sequence[Bar],
    bars_4h: Sequence[Bar],
) -> Batch134Signals:
    n = len(bars_1h)
    regime = regime_ok_series_4h_ema(bars_1h, bars_4h, ema_period=EMA_4H)
    atrs = atr_wilder_1h(bars_1h, period=ATR_N)
    closes = [float(b.close) for b in bars_1h]
    rsi = rsi_wilder(closes, RSI_PERIOD)
    entry_ok = [False] * n
    exit_ok = [False] * n
    sl_ref: list[float | None] = [None] * n
    for i in range(n):
        if not bars_1h[i].closed:
            continue
        cur = rsi[i]
        if cur is None:
            continue
        cur_f = float(cur)
        if cur_f >= EXIT_RSI:
            exit_ok[i] = True
        if i == 0:
            continue
        prev = rsi[i - 1]
        if prev is None:
            continue
        # Entry: prev < 30, curr >= 30 (cross up through 30)
        if float(prev) < ENTRY_RSI and cur_f >= ENTRY_RSI and regime[i]:
            entry_ok[i] = True
    return Batch134Signals(entry_ok=entry_ok, exit_ok=exit_ok, atr=atrs, sl_ref=sl_ref)


__all__ = [
    "ATR_N",
    "ATR_SL_MULT",
    "CELL",
    "EMA_4H",
    "ENTRY_RSI",
    "EXIT_RSI",
    "FAMILY",
    "RSI_PERIOD",
    "TIME_STOP",
    "precompute_d",
]
