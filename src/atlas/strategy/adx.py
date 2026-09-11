"""Wilder ADX / DI — locked Mid M1 / Core C3+ strength gates.

Research only. not_a_forecast. Period locked per rung (M1: ADX(14)>20).
No threshold / period grind after lock.
"""

from __future__ import annotations

from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.breakout import _true_range

ADX_PERIOD = 14
ADX_GATE_M1 = 20.0


def wilder_adx_series(
    bars: Sequence[Bar], period: int = ADX_PERIOD
) -> list[tuple[float | None, float | None, float | None]]:
    """Return per-bar (adx, plus_di, minus_di). None until Wilder warm.

    Classic Wilder:
      TR, +DM, -DM → Wilder-smoothed; +DI/−DI; DX; ADX = Wilder(DX).
    First smooth = SMA of first `period` values; then Wilder:
      s_t = s_{t-1} - (s_{t-1}/period) + x_t.
    """
    n = len(bars)
    out: list[tuple[float | None, float | None, float | None]] = [(None, None, None)] * n
    if period < 1 or n < period + 1:
        return out

    trs: list[float] = [0.0]
    plus_dm: list[float] = [0.0]
    minus_dm: list[float] = [0.0]
    for i in range(1, n):
        trs.append(_true_range(bars[i], bars[i - 1].close))
        up = float(bars[i].high) - float(bars[i - 1].high)
        down = float(bars[i - 1].low) - float(bars[i].low)
        plus_dm.append(up if up > down and up > 0 else 0.0)
        minus_dm.append(down if down > up and down > 0 else 0.0)

    # Need `period` DM/TR samples starting at index 1 → first SMA ends at index `period`
    if n <= period:
        return out

    atr = sum(trs[1 : period + 1])
    sm_plus = sum(plus_dm[1 : period + 1])
    sm_minus = sum(minus_dm[1 : period + 1])

    def _di(sm_dm: float, atr_v: float) -> float:
        if atr_v <= 0:
            return 0.0
        return 100.0 * sm_dm / atr_v

    def _dx(pdi: float, mdi: float) -> float:
        denom = pdi + mdi
        if denom <= 0:
            return 0.0
        return 100.0 * abs(pdi - mdi) / denom

    pdi = _di(sm_plus, atr)
    mdi = _di(sm_minus, atr)
    dx_vals: list[float] = []
    # First DX available at index `period`
    dx_vals.append(_dx(pdi, mdi))
    out[period] = (None, pdi, mdi)  # ADX not yet (needs period DX)

    for i in range(period + 1, n):
        atr = atr - (atr / period) + trs[i]
        sm_plus = sm_plus - (sm_plus / period) + plus_dm[i]
        sm_minus = sm_minus - (sm_minus / period) + minus_dm[i]
        pdi = _di(sm_plus, atr)
        mdi = _di(sm_minus, atr)
        dx_vals.append(_dx(pdi, mdi))
        out[i] = (None, pdi, mdi)

    # ADX: SMA of first `period` DX, then Wilder. First ADX at index 2*period - 1
    # dx_vals[0] corresponds to bar index `period`
    if len(dx_vals) < period:
        return out
    adx = sum(dx_vals[:period]) / period
    first_adx_i = period + period - 1  # 2*period - 1
    pdi0 = out[first_adx_i][1]
    mdi0 = out[first_adx_i][2]
    out[first_adx_i] = (adx, pdi0, mdi0)
    for k in range(period, len(dx_vals)):
        adx = (adx * (period - 1) + dx_vals[k]) / period
        i = period + k
        pdi_i, mdi_i = out[i][1], out[i][2]
        out[i] = (adx, pdi_i, mdi_i)
    return out


def adx_at(bars: Sequence[Bar], period: int = ADX_PERIOD) -> float | None:
    """ADX on the last bar, or None if cold."""
    series = wilder_adx_series(bars, period)
    if not series:
        return None
    return series[-1][0]


__all__ = [
    "ADX_GATE_M1",
    "ADX_PERIOD",
    "adx_at",
    "wilder_adx_series",
]
