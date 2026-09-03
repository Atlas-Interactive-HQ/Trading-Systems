"""EMA long/flat trend follower — daily closes, never short.

Research-only parallel family (not BreakoutV1, not a Phase A replacement).
Long when EMA(fast) > EMA(slow) on a *closed* bar; otherwise flat (cash).
Signal at close applies on the *next* bar open (no same-bar lookahead).

not_a_forecast. Named bull windows bias a long-only rule — say so in reports.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar, q

LONG = "long"
FLAT = "flat"


@dataclass(frozen=True)
class EmaTrendParams:
    fast: int = 12
    slow: int = 30
    confirm_closed_only: bool = True


def ema_series(closes: Sequence[float], period: int) -> list[float | None]:
    """EMA seeded with SMA of the first `period` closes. None until seeded."""
    if period < 1:
        raise ValueError(f"EMA period must be >= 1, got {period}")
    out: list[float | None] = [None] * len(closes)
    if len(closes) < period:
        return out
    seed = sum(float(closes[i]) for i in range(period)) / float(period)
    out[period - 1] = q(seed)
    k = 2.0 / (period + 1.0)
    prev = seed
    for i in range(period, len(closes)):
        prev = float(closes[i]) * k + prev * (1.0 - k)
        out[i] = q(prev)
    return out


class EmaTrendV1:
    """Daily long/flat. Never emits short. Insufficient history → flat (fail closed)."""

    def __init__(self, params: EmaTrendParams | None = None) -> None:
        self.params = params or EmaTrendParams()
        if self.params.fast < 1 or self.params.slow < 1:
            raise ValueError("EMA periods must be >= 1")
        if self.params.fast >= self.params.slow:
            raise ValueError("fast EMA period must be < slow")

    @property
    def label(self) -> str:
        return f"ema_long_flat_v1_{self.params.fast}_{self.params.slow}"

    def warmup_bars(self) -> int:
        return self.params.slow

    def desired_state(self, bars: Sequence[Bar]) -> str:
        """State implied by the last *closed* bar. `flat` if history is too short."""
        p = self.params
        if not bars:
            return FLAT
        last = bars[-1]
        if p.confirm_closed_only and not last.closed:
            return FLAT
        if len(bars) < p.slow:
            return FLAT
        closes = [float(b.close) for b in bars]
        fast = ema_series(closes, p.fast)
        slow = ema_series(closes, p.slow)
        f, s = fast[-1], slow[-1]
        if f is None or s is None:
            return FLAT
        if f > s:
            return LONG
        return FLAT
