"""#134 cell F — 1H Supertrend(10, 3.0) flip long + 4H EMA21. Paper only."""

from __future__ import annotations

from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.scalp_134_common import Batch134Signals
from atlas.strategy.scalp_dt_rvol_1h_132 import atr_wilder_1h, regime_ok_series_4h_ema
from atlas.strategy.supertrend import DEFAULT_MULT, DEFAULT_PERIOD, supertrend_bars

ST_PERIOD = DEFAULT_PERIOD  # 10
ST_MULT = DEFAULT_MULT  # 3.0
ATR_N = 14
TIME_STOP = 48
EMA_4H = 21
CELL = "F"
FAMILY = "supertrend10_3_1h_ema21_4h"


def precompute_f(
    bars_1h: Sequence[Bar],
    bars_4h: Sequence[Bar],
) -> Batch134Signals:
    n = len(bars_1h)
    regime = regime_ok_series_4h_ema(bars_1h, bars_4h, ema_period=EMA_4H)
    atrs = atr_wilder_1h(bars_1h, period=ATR_N)
    st_line, direction = supertrend_bars(bars_1h, period=ST_PERIOD, multiplier=ST_MULT)
    entry_ok = [False] * n
    exit_ok = [False] * n
    sl_ref: list[float | None] = [None] * n
    for i in range(n):
        if not bars_1h[i].closed:
            continue
        d = direction[i]
        st = st_line[i]
        sl_ref[i] = float(st) if st is not None else None
        if d is None:
            continue
        if i == 0:
            continue
        prev_d = direction[i - 1]
        if prev_d is None:
            continue
        # Flip to long
        if int(prev_d) <= 0 and int(d) == 1 and regime[i]:
            entry_ok[i] = True
        # Flip to short → exit
        if int(d) == -1:
            exit_ok[i] = True
    return Batch134Signals(entry_ok=entry_ok, exit_ok=exit_ok, atr=atrs, sl_ref=sl_ref)


__all__ = [
    "ATR_N",
    "CELL",
    "EMA_4H",
    "FAMILY",
    "ST_MULT",
    "ST_PERIOD",
    "TIME_STOP",
    "precompute_f",
]
