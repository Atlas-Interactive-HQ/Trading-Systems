"""MACD long/flat trend follower — cross above/below signal, never short.

Canonical paper rule (no prior Mid/Scalp MACD module in-repo):
  Long when MACD line crosses *above* signal; flat when crosses *below*.
  MACD(fast, slow, signal) = EMA(fast) − EMA(slow); signal = EMA(signal) of MACD.

Research only. not_a_forecast. Never places orders.
Signal at close applies on the *next* bar open (walk_long_flat).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar, q
from atlas.strategy.ema_trend import FLAT, LONG, ema_series

DEFAULT_FAST = 12
DEFAULT_SLOW = 26
DEFAULT_SIGNAL = 9


@dataclass(frozen=True)
class MacdTrendParams:
    fast: int = DEFAULT_FAST
    slow: int = DEFAULT_SLOW
    signal: int = DEFAULT_SIGNAL
    confirm_closed_only: bool = True


def macd_lines(
    closes: Sequence[float],
    *,
    fast: int,
    slow: int,
    signal: int,
) -> tuple[list[float | None], list[float | None]]:
    """Return (macd_line, signal_line). None until each series is seeded.

    MACD seeded when both EMAs exist (index slow-1). Signal is EMA(signal) of
    the MACD line, seeded with SMA of the first `signal` non-None MACD values.
    """
    if fast < 1 or slow < 1 or signal < 1:
        raise ValueError("MACD periods must be >= 1")
    if fast >= slow:
        raise ValueError("MACD fast must be < slow")
    n = len(closes)
    macd: list[float | None] = [None] * n
    sig: list[float | None] = [None] * n
    if n < slow:
        return macd, sig

    fast_e = ema_series(closes, fast)
    slow_e = ema_series(closes, slow)
    for i in range(n):
        f, s = fast_e[i], slow_e[i]
        if f is None or s is None:
            continue
        macd[i] = q(float(f) - float(s))

    # Collect indices with MACD values for signal EMA seeding.
    macd_vals: list[tuple[int, float]] = [
        (i, float(v)) for i, v in enumerate(macd) if v is not None
    ]
    if len(macd_vals) < signal:
        return macd, sig

    seed = sum(v for _, v in macd_vals[:signal]) / float(signal)
    seed_idx = macd_vals[signal - 1][0]
    sig[seed_idx] = q(seed)
    k = 2.0 / (signal + 1.0)
    prev = seed
    for j in range(signal, len(macd_vals)):
        idx, val = macd_vals[j]
        prev = val * k + prev * (1.0 - k)
        sig[idx] = q(prev)
    return macd, sig


class MacdTrendV1:
    """Long/flat on MACD×signal cross. Never emits short. Insufficient history → flat."""

    def __init__(self, params: MacdTrendParams | None = None) -> None:
        self.params = params or MacdTrendParams()
        p = self.params
        if p.fast < 1 or p.slow < 1 or p.signal < 1:
            raise ValueError("MACD periods must be >= 1")
        if p.fast >= p.slow:
            raise ValueError("MACD fast must be < slow")

    @property
    def label(self) -> str:
        p = self.params
        return f"macd_long_flat_v1_{p.fast}_{p.slow}_{p.signal}"

    def warmup_bars(self) -> int:
        # First MACD at slow; signal seeds after `signal` MACD points → slow+signal-1.
        return int(self.params.slow) + int(self.params.signal) - 1

    def desired_state(self, bars: Sequence[Bar]) -> str:
        """Causal long/flat from full prefix: cross-up enter, cross-down exit."""
        p = self.params
        if not bars:
            return FLAT
        last = bars[-1]
        if p.confirm_closed_only and not last.closed:
            return FLAT
        if len(bars) < self.warmup_bars():
            return FLAT

        closes = [float(b.close) for b in bars]
        macd, sig = macd_lines(
            closes, fast=p.fast, slow=p.slow, signal=p.signal
        )
        state = FLAT
        for i in range(len(macd)):
            cur_m, cur_s = macd[i], sig[i]
            if cur_m is None or cur_s is None:
                continue
            if i == 0:
                continue
            prev_m, prev_s = macd[i - 1], sig[i - 1]
            if prev_m is None or prev_s is None:
                continue
            pm, ps = float(prev_m), float(prev_s)
            cm, cs = float(cur_m), float(cur_s)
            if state == FLAT:
                # Cross above signal → long
                if pm <= ps and cm > cs:
                    state = LONG
            else:
                # Cross below signal → flat
                if pm >= ps and cm < cs:
                    state = FLAT
        return state


__all__ = [
    "DEFAULT_FAST",
    "DEFAULT_SLOW",
    "DEFAULT_SIGNAL",
    "FLAT",
    "LONG",
    "MacdTrendParams",
    "MacdTrendV1",
    "macd_lines",
]
