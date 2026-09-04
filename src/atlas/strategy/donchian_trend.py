"""Daily Donchian long/flat — conservative confirm, never short.

Research-only parallel family (not BreakoutV1 15m L+S, not EMA 12/30, not Phase A).
Entry: closed close strictly above the *prior* N-day high (exclusive lookback).
Exit: closed close strictly below the *prior* M-day low. Otherwise stay in state.
Never short. Insufficient history → flat. Signal at close, fill next open.

not_a_forecast. Not a mid-range buy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.breakout import donchian_prior
from atlas.strategy.ema_trend import FLAT, LONG

ENTRY_LOOKBACK = 20
EXIT_LOOKBACK = 10


@dataclass(frozen=True)
class DonchianTrendParams:
    entry_lookback: int = ENTRY_LOOKBACK
    exit_lookback: int = EXIT_LOOKBACK
    confirm_closed_only: bool = True


class DonchianLongFlatV1:
    """Daily long/flat Donchian confirm. Never emits short."""

    def __init__(self, params: DonchianTrendParams | None = None) -> None:
        self.params = params or DonchianTrendParams()
        if self.params.entry_lookback < 1 or self.params.exit_lookback < 1:
            raise ValueError("Donchian lookbacks must be >= 1")

    @property
    def label(self) -> str:
        return f"donchian_long_flat_v1_{self.params.entry_lookback}_{self.params.exit_lookback}"

    def warmup_bars(self) -> int:
        return max(self.params.entry_lookback, self.params.exit_lookback) + 1

    def desired_state(self, bars: Sequence[Bar]) -> str:
        """Path-dependent long/flat from exclusive Donchian confirms. Never short."""
        p = self.params
        state = FLAT
        if not bars:
            return FLAT
        for i in range(len(bars)):
            hist = bars[: i + 1]
            last = hist[-1]
            if p.confirm_closed_only and not last.closed:
                continue
            if state == FLAT:
                ch = donchian_prior(hist, p.entry_lookback)
                if ch is None:
                    continue
                prior_high, _prior_low = ch
                # Strictly above prior high — not an intra-channel / mid-range buy.
                if last.close > prior_high:
                    state = LONG
            else:
                ch = donchian_prior(hist, p.exit_lookback)
                if ch is None:
                    continue
                _prior_high, prior_low = ch
                if last.close < prior_low:
                    state = FLAT
            if state not in (LONG, FLAT):
                state = FLAT
        return state
