"""OKX linear USDT/USDC instrument registry — placeholders only.

Nothing in this module is a proven listing, minSz, contract value, or fee tier.
Live metadata must be probed (public instruments on the account's product gate)
before any real order. Do not treat proposed instIds as verified.

TODO(live-metadata): probe OKX EEA instruments for each proposed id and record
minSz, lotSz, tickSz, ctVal, ctType, state, and the account's fee tier.
Until that probe exists, ``listing_verified`` stays False and
``tradable_live_spec`` fails closed.
"""

from __future__ import annotations

from dataclasses import dataclass


class ListingUnverified(RuntimeError):
    """Refusing to emit a live tradable spec from placeholder metadata."""


@dataclass(frozen=True)
class InstrumentRecord:
    asset: str
    role: str
    proposed_inst_id: str
    quote: str
    inst_type: str
    linear: bool | None
    listing_verified: bool
    min_sz: None
    ct_val: None
    tick_sz: None
    lot_sz: None
    fee_tier_verified: bool
    todo: str

    def __post_init__(self) -> None:
        if self.listing_verified or self.fee_tier_verified:
            raise ListingUnverified(
                f"{self.proposed_inst_id} cannot be marked verified in the v1 stub"
            )
        if self.min_sz is not None or self.ct_val is not None:
            raise ListingUnverified("minSz/ctVal must stay unknown until probed")


def _row(
    asset: str,
    role: str,
    proposed_inst_id: str,
    quote: str,
    inst_type: str,
    linear: bool | None,
    todo: str,
) -> InstrumentRecord:
    return InstrumentRecord(
        asset=asset,
        role=role,
        proposed_inst_id=proposed_inst_id,
        quote=quote,
        inst_type=inst_type,
        linear=linear,
        listing_verified=False,
        min_sz=None,
        ct_val=None,
        tick_sz=None,
        lot_sz=None,
        fee_tier_verified=False,
        todo=todo,
    )


# Proposed ids are search keys for a future probe. Historical Mid notes mention
# DOGE-USDC and X-Perp ids; those are NOT copied here as proven linear swaps.
_PLACEHOLDERS: tuple[InstrumentRecord, ...] = (
    _row(
        "BTC",
        "reserve",
        "BTC-USDT",
        "USDT",
        "SPOT",
        None,
        "TODO: probe OKX EEA spot BTC-USDT before any reserve buy. "
        "Paper qty uses a labeled placeholder mark, not this listing.",
    ),
    _row(
        "DOGE",
        "trend",
        "DOGE-USDT-SWAP",
        "USDT",
        "SWAP",
        True,
        "TODO: probe whether a linear USDT swap is listed and tradable on this "
        "OKX EEA account. Not proven. Historical MD aliases are not a listing.",
    ),
    _row(
        "DOGE",
        "trend",
        "DOGE-USDC-SWAP",
        "USDC",
        "SWAP",
        True,
        "TODO: probe linear USDC swap / minSz. Mid history used other DOGE ids; "
        "do not assume this id exists.",
    ),
    _row(
        "SOL",
        "scalp_candidate",
        "SOL-USDT-SWAP",
        "USDT",
        "SWAP",
        True,
        "TODO: probe SOL linear USDT swap. Feasibility: ONBEKEND. Not a selection.",
    ),
    _row(
        "ETH",
        "scalp_candidate",
        "ETH-USDT-SWAP",
        "USDT",
        "SWAP",
        True,
        "TODO: probe ETH linear USDT swap. Feasibility: ONBEKEND.",
    ),
    _row(
        "PEPE",
        "scalp_candidate",
        "PEPE-USDT-SWAP",
        "USDT",
        "SWAP",
        True,
        "TODO: probe PEPE linear swap. Legacy open PEPE is excluded from this "
        "cycle. Do not adopt or close that position from here.",
    ),
)


class InstrumentRegistry:
    """In-memory stub. Paper code may read placeholders. Live specs fail closed."""

    def __init__(self, records: tuple[InstrumentRecord, ...] | None = None) -> None:
        self.records = records if records is not None else _PLACEHOLDERS
        self._by_id = {row.proposed_inst_id: row for row in self.records}

    @classmethod
    def placeholders(cls) -> "InstrumentRegistry":
        return cls()

    def get(self, proposed_inst_id: str) -> InstrumentRecord:
        try:
            return self._by_id[proposed_inst_id]
        except KeyError as exc:
            raise KeyError(
                f"no placeholder for {proposed_inst_id!r}; not inventing a listing"
            ) from exc

    def assert_paper_placeholder(self, proposed_inst_id: str) -> InstrumentRecord:
        row = self.get(proposed_inst_id)
        if row.listing_verified:
            raise ListingUnverified(row.proposed_inst_id)
        return row

    def tradable_live_spec(self, proposed_inst_id: str) -> None:
        row = self.get(proposed_inst_id)
        raise ListingUnverified(
            f"{row.proposed_inst_id} listing_verified=False. {row.todo}"
        )
