"""Daily EMA 12/30 asymmetric persist-2 entry — long/flat, never short.

Research-only (not BreakoutV1, not the weekday EMA observer, not Phase A).
FLAT → LONG only when EMA(fast) > EMA(slow) on *this* closed bar AND the prior
closed bar (persist=2). LONG → FLAT on the first closed bar where
EMA(fast) <= EMA(slow) (immediate exit; no persist on exit). Never short.

Signal at close, fill next open. Insufficient history → flat.
not_a_forecast. Persist=2 only — no 3/4/5 sweeps, no rescue filters.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.ema_trend import FLAT, LONG, ema_series

FAST = 12
SLOW = 30
ENTRY_PERSIST = 2


@dataclass(frozen=True)
class EmaPersist2Params:
    fast: int = FAST
    slow: int = SLOW
    entry_persist: int = ENTRY_PERSIST
    confirm_closed_only: bool = True


class EmaPersist2EntryV1:
    """EMA long/flat with asymmetric persist-2 entry. Never emits short."""

    def __init__(self, params: EmaPersist2Params | None = None) -> None:
        self.params = params or EmaPersist2Params()
        p = self.params
        if p.fast < 1 or p.slow < 1:
            raise ValueError("EMA periods must be >= 1")
        if p.fast >= p.slow:
            raise ValueError("fast EMA period must be < slow")
        if p.entry_persist != ENTRY_PERSIST:
            raise ValueError(
                f"entry_persist locked at {ENTRY_PERSIST} (no 3/4/5 sweeps); got {p.entry_persist}"
            )

    @property
    def label(self) -> str:
        p = self.params
        return f"ema_{p.fast}_{p.slow}_persist{p.entry_persist}_entry_v1"

    def warmup_bars(self) -> int:
        return self.params.slow + self.params.entry_persist - 1

    def desired_state(self, bars: Sequence[Bar]) -> str:
        """Path-dependent long/flat. Persist-2 entry; immediate EMA exit. Never short."""
        p = self.params
        if not bars:
            return FLAT
        closes = [float(b.close) for b in bars]
        fast = ema_series(closes, p.fast)
        slow = ema_series(closes, p.slow)
        state = FLAT
        for i in range(len(bars)):
            last = bars[i]
            if p.confirm_closed_only and not last.closed:
                continue
            f, s = fast[i], slow[i]
            ema_long = f is not None and s is not None and f > s
            if state == FLAT:
                if not ema_long:
                    continue
                if i < 1:
                    continue
                f1, s1 = fast[i - 1], slow[i - 1]
                prior_long = f1 is not None and s1 is not None and f1 > s1
                if prior_long:
                    state = LONG
            else:
                if not ema_long:
                    state = FLAT
            if state not in (LONG, FLAT):
                state = FLAT
        return state
