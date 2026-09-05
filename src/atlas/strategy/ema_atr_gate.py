"""Daily EMA 12/30 long/flat with a locked ATR/close gate.

Research-only (not BreakoutV1, not the weekday EMA observer, not Phase A).
Long iff EMA(fast) > EMA(slow) AND SMA-ATR(period)/close >= min_atr_frac
on the last *closed* bar. Else flat. Never short.
ATR is the same SMA-of-true-range used by BreakoutV1 (not Wilder).
Gate is locked at ATR(14)/close >= 0.01 — not a search grid.

Signal at close, fill next open. Insufficient ATR history → flat.
not_a_forecast.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.breakout import sma_atr
from atlas.strategy.ema_trend import FLAT, LONG, EmaTrendParams, EmaTrendV1

FAST = 12
SLOW = 30
ATR_PERIOD = 14
MIN_ATR_FRAC = 0.01


@dataclass(frozen=True)
class EmaAtrGateParams:
    fast: int = FAST
    slow: int = SLOW
    atr_period: int = ATR_PERIOD
    min_atr_frac: float = MIN_ATR_FRAC
    confirm_closed_only: bool = True


class EmaAtrGateV1:
    """EMA long/flat plus ATR/close entry gate. Never emits short."""

    def __init__(self, params: EmaAtrGateParams | None = None) -> None:
        self.params = params or EmaAtrGateParams()
        p = self.params
        if p.fast < 1 or p.slow < 1:
            raise ValueError("EMA periods must be >= 1")
        if p.fast >= p.slow:
            raise ValueError("fast EMA period must be < slow")
        if p.atr_period < 1:
            raise ValueError("ATR period must be >= 1")
        if p.min_atr_frac <= 0:
            raise ValueError("min_atr_frac must be > 0")
        self._ema = EmaTrendV1(
            EmaTrendParams(fast=p.fast, slow=p.slow, confirm_closed_only=p.confirm_closed_only)
        )

    @property
    def label(self) -> str:
        p = self.params
        frac = str(p.min_atr_frac).replace(".", "p")
        return f"ema_atr_gate_v1_{p.fast}_{p.slow}_{p.atr_period}_{frac}"

    def warmup_bars(self) -> int:
        return max(self._ema.warmup_bars(), self.params.atr_period + 1)

    def desired_state(self, bars: Sequence[Bar]) -> str:
        """LONG only if EMA is long and ATR/close clears the locked gate. Else FLAT."""
        p = self.params
        if not bars:
            return FLAT
        last = bars[-1]
        if p.confirm_closed_only and not last.closed:
            return FLAT
        if self._ema.desired_state(bars) != LONG:
            return FLAT
        atr = sma_atr(bars, p.atr_period)
        if atr is None:
            return FLAT
        close = float(last.close)
        if close <= 0:
            return FLAT
        if (atr / close) >= p.min_atr_frac:
            return LONG
        return FLAT
