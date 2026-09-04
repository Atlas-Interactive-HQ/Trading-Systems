"""Daily EMA 12/30 + Donchian 20/10 confirm — long/flat, never short.

Research-only combo (not BreakoutV1, not the weekday EMA observer, not Phase A).
Entry: EMA(fast) > EMA(slow) AND closed close strictly above the *prior* N-day high.
Exit: EMA(fast) <= EMA(slow) OR closed close strictly below the *prior* M-day low.
Hysteresis: once long, stay long between the 10-day low and 20-day high while EMA is still long.
Never short. Insufficient history → flat. Signal at close, fill next open.

not_a_forecast. Not a mid-range buy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.breakout import donchian_prior
from atlas.strategy.donchian_trend import ENTRY_LOOKBACK, EXIT_LOOKBACK
from atlas.strategy.ema_trend import FLAT, LONG, ema_series

FAST = 12
SLOW = 30


@dataclass(frozen=True)
class EmaDonchianParams:
    fast: int = FAST
    slow: int = SLOW
    entry_lookback: int = ENTRY_LOOKBACK
    exit_lookback: int = EXIT_LOOKBACK
    confirm_closed_only: bool = True


class EmaDonchianConfirmV1:
    """Daily long/flat: EMA trend AND Donchian confirm. Never emits short."""

    def __init__(self, params: EmaDonchianParams | None = None) -> None:
        self.params = params or EmaDonchianParams()
        p = self.params
        if p.fast < 1 or p.slow < 1:
            raise ValueError("EMA periods must be >= 1")
        if p.fast >= p.slow:
            raise ValueError("fast EMA period must be < slow")
        if p.entry_lookback < 1 or p.exit_lookback < 1:
            raise ValueError("Donchian lookbacks must be >= 1")

    @property
    def label(self) -> str:
        p = self.params
        return (
            f"ema_donchian_confirm_v1_{p.fast}_{p.slow}_{p.entry_lookback}_{p.exit_lookback}"
        )

    def warmup_bars(self) -> int:
        p = self.params
        return max(p.slow, p.entry_lookback + 1, p.exit_lookback + 1)

    def desired_state(self, bars: Sequence[Bar]) -> str:
        """Path-dependent long/flat. Never short. Unclosed last bar does not update state."""
        p = self.params
        if not bars:
            return FLAT
        closes = [float(b.close) for b in bars]
        fast = ema_series(closes, p.fast)
        slow = ema_series(closes, p.slow)
        state = FLAT
        for i in range(len(bars)):
            hist = bars[: i + 1]
            last = hist[-1]
            if p.confirm_closed_only and not last.closed:
                continue
            f, s = fast[i], slow[i]
            ema_long = f is not None and s is not None and f > s
            if state == FLAT:
                if not ema_long:
                    continue
                ch = donchian_prior(hist, p.entry_lookback)
                if ch is None:
                    continue
                prior_high, _prior_low = ch
                if last.close > prior_high:
                    state = LONG
            else:
                if not ema_long:
                    state = FLAT
                    continue
                ch = donchian_prior(hist, p.exit_lookback)
                if ch is None:
                    continue
                _prior_high, prior_low = ch
                if last.close < prior_low:
                    state = FLAT
            if state not in (LONG, FLAT):
                state = FLAT
        return state
