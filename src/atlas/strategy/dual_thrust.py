"""Dual Thrust long/flat — HH-LL range breakout, never short.

LOCKED Scalp #83 seed: lookback N, k1, k2.
  Range = HH - LL over *prior* N bars (exclusive of decision bar).
  Buy  = open + k1 * Range
  Sell = open - k2 * Range
Long when closed close breaks above Buy; flat when closed close breaks below Sell.
Otherwise stay in state. Insufficient history → flat. Never short.
Signal at close, fill next open. not_a_forecast.

Seed lock: N=20, k1=0.5, k2=0.5 — no post-FAIL grind.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.breakout import donchian_prior
from atlas.strategy.ema_trend import FLAT, LONG

LOOKBACK = 20
K1 = 0.5
K2 = 0.5


@dataclass(frozen=True)
class DualThrustParams:
    lookback: int = LOOKBACK
    k1: float = K1
    k2: float = K2
    confirm_closed_only: bool = True


def prior_hh_ll_range(bars: Sequence[Bar], lookback: int) -> float | None:
    """HH-LL over the lookback bars *before* the last bar (LOCKED formula)."""
    hl = donchian_prior(bars, lookback)
    if hl is None:
        return None
    hh, ll = hl
    return hh - ll


class DualThrustLongFlatV1:
    """Path-dependent Dual Thrust long/flat. Never emits short."""

    def __init__(self, params: DualThrustParams | None = None) -> None:
        self.params = params or DualThrustParams()
        if self.params.lookback < 1:
            raise ValueError("Dual Thrust lookback must be >= 1")
        if self.params.k1 < 0 or self.params.k2 < 0:
            raise ValueError("Dual Thrust k1/k2 must be >= 0")

    @property
    def label(self) -> str:
        p = self.params
        return f"dual_thrust_long_flat_v1_n{p.lookback}_k1{p.k1}_k2{p.k2}"

    def warmup_bars(self) -> int:
        return self.params.lookback + 1

    def ranges_at(self, bars: Sequence[Bar]) -> tuple[float, float] | None:
        """Return (buy_range, sell_range) for the last bar, or None if cold."""
        p = self.params
        if not bars:
            return None
        last = bars[-1]
        rng = prior_hh_ll_range(bars, p.lookback)
        if rng is None:
            return None
        buy = last.open + p.k1 * rng
        sell = last.open - p.k2 * rng
        return buy, sell

    def desired_state(self, bars: Sequence[Bar]) -> str:
        """Path-dependent long/flat from Dual Thrust breakouts. Never short."""
        p = self.params
        state = FLAT
        if not bars:
            return FLAT
        for i in range(len(bars)):
            hist = bars[: i + 1]
            last = hist[-1]
            if p.confirm_closed_only and not last.closed:
                continue
            ranges = self.ranges_at(hist)
            if ranges is None:
                continue
            buy, sell = ranges
            if state == FLAT:
                if last.close > buy:
                    state = LONG
            else:
                if last.close < sell:
                    state = FLAT
            if state not in (LONG, FLAT):
                state = FLAT
        return state


__all__ = [
    "K1",
    "K2",
    "LOOKBACK",
    "DualThrustLongFlatV1",
    "DualThrustParams",
    "FLAT",
    "LONG",
    "prior_hh_ll_range",
]
