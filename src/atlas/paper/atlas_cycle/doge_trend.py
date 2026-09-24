"""DOGE trend skeleton: 4H veto, 1H filter, 15m breakout + first retest.

Primary entry is the first retest of a 15m Donchian breakout. Direct breakout
entry is an ablation flag (default off). Long only. No shorts, no averaging
down, no martingale.

This is a deterministic rule skeleton for paper wiring. It is not an edge
claim and it does not read news or a model.

Reuses ``donchian_prior`` from the existing breakout module. Higher-timeframe
bars are supplied by the caller; missing history fails closed (veto / no trade).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Sequence

from atlas.paper.atlas_cycle.money import D
from atlas.paper.types import Bar
from atlas.strategy.breakout import donchian_prior


@dataclass(frozen=True)
class DogeTrendParams:
    lookback_15m: int = 16
    retest_tolerance: Decimal = Decimal("0.001")
    max_retest_wait_bars: int = 8
    direct_breakout: bool = False


@dataclass(frozen=True)
class DogeDecision:
    action: str  # enter_long | exit | none
    stop: Decimal | None
    reason: str
    ablation: str | None = None


class DogeTrendStrategy:
    """One DOGE cycle. State is the breakout→retest setup, not a position stack."""

    def __init__(self, params: DogeTrendParams | None = None) -> None:
        self.params = params or DogeTrendParams()
        if self.params.lookback_15m < 2:
            raise ValueError("lookback_15m must be >= 2")
        if self.params.retest_tolerance < 0:
            raise ValueError("retest tolerance must be >= 0")
        self._phase = "waiting"
        self._level: float | None = None
        self._breakout_low: float | None = None
        self._wait = 0

    def reset(self) -> None:
        self._phase = "waiting"
        self._level = None
        self._breakout_low = None
        self._wait = 0

    def evaluate(
        self,
        bars_15m: Sequence[Bar],
        bars_1h: Sequence[Bar],
        bars_4h: Sequence[Bar],
        *,
        position_open: bool,
        stop: Decimal | None = None,
    ) -> DogeDecision:
        if not bars_15m:
            return DogeDecision("none", None, "no_15m")
        last = bars_15m[-1]
        if position_open:
            if stop is not None and D(last.close) < stop:
                return DogeDecision("exit", stop, "stop_close")
            return DogeDecision("none", stop, "hold")

        veto, veto_reason = four_h_veto(bars_4h)
        if veto:
            self.reset()
            return DogeDecision("none", None, veto_reason)
        allowed, filter_reason = one_h_allows_long(bars_1h)
        if not allowed:
            self.reset()
            return DogeDecision("none", None, filter_reason)

        channel = donchian_prior(bars_15m, self.params.lookback_15m)
        if channel is None:
            return DogeDecision("none", None, "insufficient_15m")
        prior_high = channel[0]

        if self._phase == "waiting":
            if last.close > prior_high:
                if self.params.direct_breakout:
                    stop_px = _stop_below(last.close, last.low)
                    self.reset()
                    return DogeDecision(
                        "enter_long",
                        stop_px,
                        "direct_breakout_ablation",
                        ablation="direct_breakout",
                    )
                self._phase = "seen"
                self._level = prior_high
                self._breakout_low = last.low
                self._wait = 0
                return DogeDecision("none", None, "breakout_seen_wait_retest")
            return DogeDecision("none", None, "no_breakout")

        self._wait += 1
        level = self._level if self._level is not None else prior_high
        if last.close < level:
            self.reset()
            return DogeDecision("none", None, "retest_invalidated")
        tol = float(self.params.retest_tolerance)
        touched = last.low <= level * (1.0 + tol)
        held = last.close > level
        if touched and held:
            floor = last.low
            if self._breakout_low is not None:
                floor = min(floor, self._breakout_low)
            stop_px = _stop_below(last.close, floor)
            self.reset()
            return DogeDecision("enter_long", stop_px, "first_retest")
        if self._wait >= self.params.max_retest_wait_bars:
            self.reset()
            return DogeDecision("none", None, "retest_timeout")
        return DogeDecision("none", None, "waiting_retest")


def four_h_veto(bars_4h: Sequence[Bar]) -> tuple[bool, str]:
    """Block longs when 4H history is missing or the last close is not above
    the prior 4H bar's midpoint. Fail closed.
    """
    if len(bars_4h) < 2:
        return True, "insufficient_4h"
    prior = bars_4h[-2]
    last = bars_4h[-1]
    midpoint = (prior.high + prior.low) / 2.0
    if last.close <= midpoint:
        return True, "4h_veto"
    return False, "4h_clear"


def one_h_allows_long(bars_1h: Sequence[Bar]) -> tuple[bool, str]:
    """1H filter: last close must be above the prior 1H bar's midpoint."""
    if len(bars_1h) < 2:
        return False, "insufficient_1h"
    prior = bars_1h[-2]
    last = bars_1h[-1]
    midpoint = (prior.high + prior.low) / 2.0
    if last.close > midpoint:
        return True, "1h_pass"
    return False, "1h_block"


def _stop_below(close: float, floor: float) -> Decimal:
    if floor < close:
        return D(floor)
    # Degenerate bar: keep a stop strictly under the close. Not a widen of risk;
    # the sizer still uses this distance, and leverage stays capped.
    return D(close) * D("0.99")
