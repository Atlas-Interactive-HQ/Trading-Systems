"""#134 cell H — 1H MACD hist cross up 0 + RVOL>1 + 4H EMA21. Paper only."""

from __future__ import annotations

from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.macd_trend import macd_lines
from atlas.strategy.rvol import rvol_series
from atlas.strategy.scalp_134_common import Batch134Signals
from atlas.strategy.scalp_dt_rvol_1h_132 import atr_wilder_1h, regime_ok_series_4h_ema

MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
RVOL_N = 20
RVOL_GATE = 1.0
ATR_N = 14
ATR_SL_MULT = 1.5
TIME_STOP = 24
EMA_4H = 21
CELL = "H"
FAMILY = "macd_hist0_rvol_gt1_1h_ema21_4h"


def precompute_h(
    bars_1h: Sequence[Bar],
    bars_4h: Sequence[Bar],
) -> Batch134Signals:
    n = len(bars_1h)
    regime = regime_ok_series_4h_ema(bars_1h, bars_4h, ema_period=EMA_4H)
    atrs = atr_wilder_1h(bars_1h, period=ATR_N)
    rvols = rvol_series(bars_1h, RVOL_N)
    closes = [float(b.close) for b in bars_1h]
    macd, sig = macd_lines(
        closes, fast=MACD_FAST, slow=MACD_SLOW, signal=MACD_SIGNAL
    )
    entry_ok = [False] * n
    exit_ok = [False] * n
    sl_ref: list[float | None] = [None] * n
    for i in range(n):
        if not bars_1h[i].closed:
            continue
        m, s = macd[i], sig[i]
        if m is None or s is None:
            continue
        hist = float(m) - float(s)
        if i == 0:
            continue
        pm, ps = macd[i - 1], sig[i - 1]
        if pm is None or ps is None:
            continue
        prev_hist = float(pm) - float(ps)
        rvol = rvols[i]
        rvol_ok = rvol is not None and float(rvol) > RVOL_GATE
        # Hist crosses up through 0
        if prev_hist < 0.0 and hist >= 0.0 and rvol_ok and regime[i]:
            entry_ok[i] = True
        # Hist crosses down through 0
        if prev_hist > 0.0 and hist <= 0.0:
            exit_ok[i] = True
    return Batch134Signals(entry_ok=entry_ok, exit_ok=exit_ok, atr=atrs, sl_ref=sl_ref)


__all__ = [
    "ATR_N",
    "ATR_SL_MULT",
    "CELL",
    "EMA_4H",
    "FAMILY",
    "MACD_FAST",
    "MACD_SIGNAL",
    "MACD_SLOW",
    "RVOL_GATE",
    "RVOL_N",
    "TIME_STOP",
    "precompute_h",
]
