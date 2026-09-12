"""#134 cell J — 1H session VWAP pullback + RVOL>1 + 4H EMA21. Paper only."""

from __future__ import annotations

from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.rvol import rvol_series
from atlas.strategy.scalp_134_common import Batch134Signals
from atlas.strategy.scalp_dt_rvol_1h_132 import atr_wilder_1h, regime_ok_series_4h_ema
from atlas.strategy.session_vwap import session_vwap_series

RVOL_N = 20
RVOL_GATE = 1.0
ATR_N = 14
ATR_SL_MULT = 1.0
R = 1.5
TIME_STOP = 24
EMA_4H = 21
CELL = "J"
FAMILY = "vwap_pullback_rvol_gt1_1h_ema21_4h"


def precompute_j(
    bars_1h: Sequence[Bar],
    bars_4h: Sequence[Bar],
) -> Batch134Signals:
    n = len(bars_1h)
    regime = regime_ok_series_4h_ema(bars_1h, bars_4h, ema_period=EMA_4H)
    atrs = atr_wilder_1h(bars_1h, period=ATR_N)
    rvols = rvol_series(bars_1h, RVOL_N)
    vwaps = session_vwap_series(bars_1h)
    entry_ok = [False] * n
    exit_ok = [False] * n
    sl_ref: list[float | None] = [None] * n
    for i in range(n):
        bar = bars_1h[i]
        if not bar.closed:
            continue
        if i == 0:
            continue
        vwap = vwaps[i]
        prev_vwap = vwaps[i - 1]
        if vwap is None or prev_vwap is None:
            continue
        prev_c = float(bars_1h[i - 1].close)
        c = float(bar.close)
        h = float(bar.high)
        l = float(bar.low)
        rvol = rvols[i]
        rvol_ok = rvol is not None and float(rvol) > RVOL_GATE
        # Bias: close > session VWAP; prior was above VWAP
        prior_above = prev_c > float(prev_vwap)
        this_above = c > float(vwap)
        # Pullback touch: low <= VWAP <= high, or close crosses back to/above VWAP
        touches = l <= float(vwap) <= h
        prev_below_or_eq = prev_c <= float(prev_vwap)
        cross_back = prev_below_or_eq and c >= float(vwap)
        pullback = touches or cross_back
        if regime[i] and rvol_ok and this_above and prior_above and pullback:
            entry_ok[i] = True
    return Batch134Signals(entry_ok=entry_ok, exit_ok=exit_ok, atr=atrs, sl_ref=sl_ref)


__all__ = [
    "ATR_N",
    "ATR_SL_MULT",
    "CELL",
    "EMA_4H",
    "FAMILY",
    "R",
    "RVOL_GATE",
    "RVOL_N",
    "TIME_STOP",
    "precompute_j",
]
