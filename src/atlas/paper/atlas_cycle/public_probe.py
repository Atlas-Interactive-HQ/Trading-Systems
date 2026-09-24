"""Public OKX swap metadata captured for the paper feasibility table.

Fetched without API keys from ``https://eea.okx.com`` on 2026-09-24:

- ``/api/v5/public/instruments?instType=SWAP``
- ``/api/v5/market/ticker``

The registry stub still has ``listing_verified=false`` and empty ``min_sz``.
A public payload is not an account permission, not a fee tier, and not a
live order spec. ``tradable_live_spec`` keeps failing closed.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from atlas.paper.atlas_cycle.money import D

PROBE_ASOF = "2026-09-24"
PROBE_SOURCE = "https://eea.okx.com/api/v5/public/instruments"
TICKER_SOURCE = "https://eea.okx.com/api/v5/market/ticker"


@dataclass(frozen=True)
class PublicSwapSnapshot:
    asset: str
    inst_id: str
    state: str
    min_sz: Decimal
    lot_sz: Decimal
    tick_sz: Decimal
    ct_val: Decimal
    ct_val_ccy: str
    exchange_max_lever: Decimal
    last_price: Decimal
    ticker_ts_ms: int

    @property
    def min_coin(self) -> Decimal:
        """Minimum coin quantity for one minSz order. Not a live spec."""
        return self.min_sz * self.ct_val

    @property
    def lot_coin(self) -> Decimal:
        return self.lot_sz * self.ct_val


# Numbers below are the public response, stored so tests do not need a network.
PUBLIC_SWAPS: dict[str, PublicSwapSnapshot] = {
    "SOL": PublicSwapSnapshot(
        "SOL",
        "SOL-USDT-SWAP",
        "live",
        D("0.01"),
        D("0.01"),
        D("0.01"),
        D("1"),
        "SOL",
        D("100"),
        D("115.5"),
        1790236947268,
    ),
    "ETH": PublicSwapSnapshot(
        "ETH",
        "ETH-USDT-SWAP",
        "live",
        D("0.01"),
        D("0.01"),
        D("0.01"),
        D("0.1"),
        "ETH",
        D("100"),
        D("2692.17"),
        1790236947166,
    ),
    "PEPE": PublicSwapSnapshot(
        "PEPE",
        "PEPE-USDT-SWAP",
        "live",
        D("0.1"),
        D("0.1"),
        D("0.000000001"),
        D("10000000"),
        "PEPE",
        D("50"),
        D("0.000004409"),
        1790236948370,
    ),
}
