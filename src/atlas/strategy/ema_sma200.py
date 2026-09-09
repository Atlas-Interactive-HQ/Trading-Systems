"""Daily EMA 12/30 + SMA(200) regime filter — long/flat, never short.

Research-only (not BreakoutV1, not the weekday EMA observer, not Phase A).
Long iff EMA(fast) > EMA(slow) AND close > SMA(sma_period) on the last *closed*
bar. Else flat. Never short. Needs pad ≥ warmup (default 220 days) so SMA(200)
is seeded before the scored window.

Signal at close, fill next open. Insufficient history → flat.
not_a_forecast. Docs-only CLEAR/FAIL — do not promote.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar, q
from atlas.strategy.ema_trend import FLAT, LONG, EmaTrendParams, EmaTrendV1

FAST = 12
SLOW = 30
SMA_PERIOD = 200
WARMUP_DAYS = 220


def sma_at(closes: Sequence[float], period: int) -> float | None:
    """Simple moving average of the last `period` closes. None if too short."""
    if period < 1:
        raise ValueError(f"SMA period must be >= 1, got {period}")
    if len(closes) < period:
        return None
    window = closes[-period:]
    return q(sum(float(x) for x in window) / float(period))


@dataclass(frozen=True)
class EmaSma200Params:
    fast: int = FAST
    slow: int = SLOW
    sma_period: int = SMA_PERIOD
    confirm_closed_only: bool = True


class EmaSma200RegimeV1:
    """EMA long/flat plus close > SMA(200) regime. Never emits short."""

    def __init__(self, params: EmaSma200Params | None = None) -> None:
        self.params = params or EmaSma200Params()
        p = self.params
        if p.fast < 1 or p.slow < 1:
            raise ValueError("EMA periods must be >= 1")
        if p.fast >= p.slow:
            raise ValueError("fast EMA period must be < slow")
        if p.sma_period < 1:
            raise ValueError("SMA period must be >= 1")
        self._ema = EmaTrendV1(
            EmaTrendParams(fast=p.fast, slow=p.slow, confirm_closed_only=p.confirm_closed_only)
        )

    @property
    def label(self) -> str:
        p = self.params
        return f"ema_sma200_regime_v1_{p.fast}_{p.slow}_{p.sma_period}"

    def warmup_bars(self) -> int:
        return max(self._ema.warmup_bars(), self.params.sma_period, WARMUP_DAYS)

    def desired_state(self, bars: Sequence[Bar]) -> str:
        """LONG only if EMA is long and close > SMA(200). Else FLAT."""
        p = self.params
        if not bars:
            return FLAT
        last = bars[-1]
        if p.confirm_closed_only and not last.closed:
            return FLAT
        if self._ema.desired_state(bars) != LONG:
            return FLAT
        closes = [float(b.close) for b in bars]
        sma = sma_at(closes, p.sma_period)
        if sma is None:
            return FLAT
        if float(last.close) > sma:
            return LONG
        return FLAT
