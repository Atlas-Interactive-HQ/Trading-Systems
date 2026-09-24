"""Scalp research rules for SOL, ETH, and PEPE. Default off.

Same signal for every candidate. No extra coins. Long only. The coordinator
enforces one slot, the +1R DOGE window, the 5-scalp cap, and the two-loss
streak. This module only reads closed bars.

No edge is claimed. Listings are unverified. The legacy live PEPE position
is not read or closed here.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Sequence

from atlas.paper.atlas_cycle.money import D
from atlas.paper.types import Bar
from atlas.strategy.breakout import donchian_prior

SCALP_CANDIDATES = ("SOL", "ETH", "PEPE")
_SYMBOL = {
    "SOL": "SOL-USDT-SWAP",
    "ETH": "ETH-USDT-SWAP",
    "PEPE": "PEPE-USDT-SWAP",
}


@dataclass(frozen=True)
class ScalpDecision:
    action: str  # enter_long | exit | none
    symbol: str | None
    asset: str | None
    stop: Decimal | None
    reason: str
    fill_ref: Decimal | None = None


class ScalpMomentumStrategy:
    def __init__(self, *, lookback: int = 8, asset: str = "SOL") -> None:
        if lookback < 2:
            raise ValueError("scalp lookback must be >= 2")
        self.lookback = lookback
        self.asset = _require_asset(asset)

    def evaluate(
        self,
        bars: Sequence[Bar],
        *,
        enabled: bool,
        doge_cycle_healthy: bool,
        asset: str | None = None,
    ) -> ScalpDecision:
        chosen = _require_asset(asset or self.asset)
        symbol = _SYMBOL[chosen]
        if not enabled:
            return ScalpDecision("none", None, chosen, None, "scalp_disabled")
        if not doge_cycle_healthy:
            return ScalpDecision("none", symbol, chosen, None, "doge_cycle_not_healthy")
        if not bars or not bars[-1].closed:
            return ScalpDecision("none", symbol, chosen, None, "open_bar")
        channel = donchian_prior(bars, self.lookback)
        if channel is None:
            return ScalpDecision("none", symbol, chosen, None, "insufficient_bars")
        last = bars[-1]
        if last.close > channel[0] and last.close > last.open and last.low < last.close:
            return ScalpDecision(
                "enter_long",
                symbol,
                chosen,
                D(last.low),
                "momentum_breakout",
                fill_ref=D(last.close),
            )
        return ScalpDecision("none", symbol, chosen, None, "no_breakout")

    def manage_open(
        self,
        bar: Bar,
        *,
        entry: Decimal,
        stop: Decimal,
        r_dist: Decimal,
        entry_index: int,
        index: int,
        max_hold_bars: int = 8,
    ) -> ScalpDecision:
        """Stop before target. A same-bar high does not cancel a stop touch."""
        if not bar.closed:
            return ScalpDecision("none", None, self.asset, stop, "open_bar")
        if bar.open <= float(stop):
            return ScalpDecision(
                "exit", None, self.asset, stop, "stop_gap", fill_ref=D(bar.open)
            )
        if bar.low <= float(stop):
            return ScalpDecision(
                "exit", None, self.asset, stop, "stop", fill_ref=stop
            )
        target = entry + D("1.5") * r_dist
        if D(bar.high) >= target:
            return ScalpDecision(
                "exit", None, self.asset, stop, "target_1_5r", fill_ref=target
            )
        if index - entry_index >= max_hold_bars:
            return ScalpDecision(
                "exit", None, self.asset, stop, "max_hold", fill_ref=D(bar.close)
            )
        return ScalpDecision("none", None, self.asset, stop, "hold")


def _require_asset(asset: str) -> str:
    key = asset.upper()
    if key not in SCALP_CANDIDATES:
        raise ValueError(
            f"scalp asset {asset!r} is not in {SCALP_CANDIDATES}; v1 does not rotate coins"
        )
    return key


def symbol_for(asset: str) -> str:
    return _SYMBOL[_require_asset(asset)]
