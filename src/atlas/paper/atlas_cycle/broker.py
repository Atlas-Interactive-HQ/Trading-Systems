"""Simulated broker for Atlas Cycle v1. No network. No API keys.

Fee and slippage match the existing paper fill formula
(``atlas.paper.fills``), computed in Decimal:

    buy  fill = ref * (1 + slippage_bps / 10_000)
    sell fill = ref * (1 - slippage_bps / 10_000)
    fee       = abs(qty * fill) * taker_fee_rate

Assumptions (labeled, not a measured fee tier):

- Taker both sides. Maker / rebate is not assumed.
- DOGE slippage default 5 bps per fill. Scalp default 10 bps per fill.
- Funding is unknown and is not credited. Do not promote while funding is
  unknown.
- USDT/USDC/EUR 1:1 inside the paper book.

LIVE execution is refused before any fill is built.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from atlas.paper.atlas_cycle.enums import ExecutionMode
from atlas.paper.atlas_cycle.instruments import InstrumentRegistry
from atlas.paper.atlas_cycle.money import D, q


class LiveExecutionRefused(RuntimeError):
    """LIVE HOLD. PAPER_PASS is not a live arm. No order is built."""


class ShortsForbidden(RuntimeError):
    """v1 is long-only."""


class UnknownInstrument(RuntimeError):
    """Symbol is not even a paper placeholder."""


@dataclass(frozen=True)
class PaperFill:
    ts_ms: int
    symbol: str
    sleeve: str
    side: str
    qty: Decimal
    price: Decimal
    fee: Decimal
    slippage_bps: Decimal
    fee_rate: Decimal
    reason: str
    kind: str
    listing_verified: bool
    execution_mode: str
    assumptions: str


def parse_execution_mode(value: str) -> ExecutionMode:
    """Accept BACKTEST or PAPER. Any LIVE spelling is refused."""
    text = str(value).strip().upper()
    if text == "LIVE" or text.startswith("LIVE"):
        raise LiveExecutionRefused(
            "LIVE HOLD remains. Atlas Cycle v1 refuses execution_mode LIVE. "
            "PAPER_PASS ≠ live-arm. No order will be sent."
        )
    if text == "BACKTEST":
        return ExecutionMode.BACKTEST
    if text == "PAPER":
        return ExecutionMode.PAPER
    raise LiveExecutionRefused(
        f"execution_mode {value!r} is not BACKTEST or PAPER; refusing"
    )


class SimulatedBroker:
    """In-process fills only. Holds no credentials."""

    def __init__(
        self,
        execution_mode: ExecutionMode | str,
        *,
        taker_fee_rate: object = "0.0005",
        doge_slippage_bps: object = "5",
        scalp_slippage_bps: object = "10",
        registry: InstrumentRegistry | None = None,
        seed: int = 20260924,
    ) -> None:
        if isinstance(execution_mode, ExecutionMode):
            self.execution_mode = execution_mode
        else:
            self.execution_mode = parse_execution_mode(str(execution_mode))
        self.taker_fee_rate = D(taker_fee_rate)
        self.doge_slippage_bps = D(doge_slippage_bps)
        self.scalp_slippage_bps = D(scalp_slippage_bps)
        if self.taker_fee_rate < 0 or self.doge_slippage_bps < 0 or self.scalp_slippage_bps < 0:
            raise ValueError("fee and slippage must be >= 0")
        self.registry = registry or InstrumentRegistry.placeholders()
        self.seed = int(seed)
        self.assumptions = (
            "ASSUMPTION taker both sides; "
            f"DOGE slip {self.doge_slippage_bps} bps; "
            f"scalp slip {self.scalp_slippage_bps} bps; "
            "funding unknown (not credited); fee tier not measured; "
            "no API keys"
        )

    def fill_market(
        self,
        *,
        ts_ms: int,
        symbol: str,
        sleeve: str,
        side: str,
        qty: object,
        ref_price: object,
        kind: str,
        reason: str,
    ) -> PaperFill:
        if self.execution_mode not in (ExecutionMode.BACKTEST, ExecutionMode.PAPER):
            raise LiveExecutionRefused("broker mode is not paper/backtest")
        side_n = side.lower()
        if side_n not in ("buy", "sell"):
            raise ValueError(f"side must be buy|sell, got {side!r}")
        if kind == "entry" and side_n != "buy":
            raise ShortsForbidden("v1 entries are long-only (buy to open)")
        if kind == "exit" and side_n != "sell":
            raise ShortsForbidden("v1 exits are sells of longs only")
        if sleeve == "btc":
            raise ShortsForbidden("broker does not sell or trade the BTC reserve")
        row = self.registry.assert_paper_placeholder(symbol)
        if sleeve == "doge" and row.asset != "DOGE":
            raise UnknownInstrument(f"{symbol} is not a DOGE placeholder")
        if sleeve == "scalp" and row.role != "scalp_candidate":
            raise UnknownInstrument(f"{symbol} is not a scalp candidate placeholder")
        quantity = D(qty)
        ref = D(ref_price)
        if quantity <= 0 or ref <= 0:
            raise ValueError("qty and ref price must be positive")
        slip = self.doge_slippage_bps if sleeve == "doge" else self.scalp_slippage_bps
        sign = D("1") if side_n == "buy" else D("-1")
        price = q(ref * (D("1") + sign * slip / D("10000")))
        fee = q(abs(quantity * price) * self.taker_fee_rate)
        return PaperFill(
            ts_ms=int(ts_ms),
            symbol=symbol,
            sleeve=sleeve,
            side=side_n,
            qty=quantity,
            price=price,
            fee=fee,
            slippage_bps=slip,
            fee_rate=self.taker_fee_rate,
            reason=reason,
            kind=kind,
            listing_verified=False,
            execution_mode=self.execution_mode.value,
            assumptions=self.assumptions,
        )
