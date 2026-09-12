"""#134 cell I — 15m Dual Thrust N20 k0.5 RVOL>1 + 1H EMA21 (not 4H). Paper only.

Different from #130 (N4, RVOL 1.2, 1.5R/sellline). Here: NO sell-line TP, NO 1.5R;
exits = SL (SellLine/ATR guard) + 1H close<EMA21 flip + ts=64×15m.
"""

from __future__ import annotations

from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.dual_thrust import DualThrustLongFlatV1, DualThrustParams
from atlas.strategy.rvol import rvol_series
from atlas.strategy.scalp_134_common import Batch134Signals
from atlas.strategy.scalp_dt_rvol_15m_130 import atr_wilder_15m, regime_ok_series_1h_ema

N = 20
K1 = 0.5
K2 = 0.5
RVOL_N = 20
RVOL_GATE = 1.0
EMA_1H = 21
ATR_N = 14
ATR_SL_MULT = 1.0  # SellLine then ATR guard (same as 130/132 resolve)
TIME_STOP = 64
CELL = "I"
FAMILY = "dt_n20_k0505_rvol20_gt10_ema21_1h_regime_15m_no_tp"


def precompute_i(
    bars_15m: Sequence[Bar],
    bars_1h: Sequence[Bar],
) -> Batch134Signals:
    n = len(bars_15m)
    regime = regime_ok_series_1h_ema(bars_15m, bars_1h, ema_period=EMA_1H)
    atrs = atr_wilder_15m(bars_15m, period=ATR_N)
    rvols = rvol_series(bars_15m, RVOL_N)
    inner = DualThrustLongFlatV1(
        DualThrustParams(lookback=N, k1=K1, k2=K2, confirm_closed_only=True)
    )
    entry_ok = [False] * n
    exit_ok = [False] * n
    sl_ref: list[float | None] = [None] * n
    for i in range(n):
        bar = bars_15m[i]
        if not bar.closed:
            continue
        hist = bars_15m[: i + 1]
        ranges = inner.ranges_at(hist)
        if ranges is None:
            continue
        bl, sl = ranges
        sl_ref[i] = float(sl)
        c = float(bar.close)
        buy = c > float(bl)
        rvol = rvols[i]
        rvol_ok = rvol is not None and float(rvol) > RVOL_GATE
        if regime[i] and buy and rvol_ok:
            entry_ok[i] = True
        # Regime flip exit: 1H close < EMA21 (regime False while in position)
        if not regime[i]:
            exit_ok[i] = True
    return Batch134Signals(entry_ok=entry_ok, exit_ok=exit_ok, atr=atrs, sl_ref=sl_ref)


__all__ = [
    "ATR_N",
    "ATR_SL_MULT",
    "CELL",
    "EMA_1H",
    "FAMILY",
    "K1",
    "K2",
    "N",
    "RVOL_GATE",
    "RVOL_N",
    "TIME_STOP",
    "precompute_i",
]
