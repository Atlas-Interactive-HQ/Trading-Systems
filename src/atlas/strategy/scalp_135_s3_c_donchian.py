"""#135 S3 — C Donchian(20) ENTRY + A-style exits (fixed SL / EMA-flip / ts168).

NO 1.5R TP. NO extra ATR trail. Paper only. Do not grind Donchian N.
"""

from __future__ import annotations

from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.breakout import donchian_prior
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

LOOKBACK = 20
CELL = "C"
SID = "S3"
FAMILY = "donchian20_mid_sl_1h_ema21_4h_emaflip_ts168"
EXIT_MODE = "a_style_fixed_sl"


def precompute_s3_c(
    bars_1h: Sequence[Bar],
    bars_4h: Sequence[Bar],
) -> Scalp135Signals:
    n = len(bars_1h)
    regime = regime_ok_series_4h_ema(bars_1h, bars_4h, ema_period=EMA_4H)
    flip = regime_flip_series_4h_ema(bars_1h, bars_4h, ema_period=EMA_4H)
    atrs = atr_wilder_1h(bars_1h, period=ATR_N)
    entry_ok = [False] * n
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
    "LOOKBACK",
    "SID",
    "TIME_STOP",
    "precompute_s3_c",
]
