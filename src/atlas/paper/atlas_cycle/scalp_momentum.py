"""Optional scalp skeleton. Default off.

Candidates are SOL, ETH, PEPE — selectable, not auto-rotated. A signal exists
only when ``enabled`` is true and the caller reports the DOGE cycle healthy.
Long only. One slot is enforced by the coordinator, not by stacking here.

No edge is claimed. Listings are unverified.
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
    action: str  # enter_long | none
    symbol: str | None
    asset: str | None
    stop: Decimal | None
    reason: str


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
            return ScalpDecision("none", None, chosen, None, "doge_cycle_not_healthy")
        channel = donchian_prior(bars, self.lookback)
        if channel is None or not bars:
            return ScalpDecision("none", symbol, chosen, None, "insufficient_bars")
        last = bars[-1]
        if last.close > channel[0]:
            stop = D(last.low) if last.low < last.close else D(last.close) * D("0.99")
            return ScalpDecision("enter_long", symbol, chosen, stop, "momentum_breakout")
        return ScalpDecision("none", symbol, chosen, None, "no_breakout")


def _require_asset(asset: str) -> str:
    key = asset.upper()
    if key not in SCALP_CANDIDATES:
        raise ValueError(
            f"scalp asset {asset!r} is not in {SCALP_CANDIDATES}; v1 does not rotate coins"
        )
    return key
