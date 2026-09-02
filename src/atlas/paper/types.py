"""Shared paper types. UTC timestamps in epoch milliseconds."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


def q(x: float, nd: int = 8) -> float:
    """Round for stable cash/px math (same inputs → same numbers)."""
    return round(float(x), nd)


class Side(str, Enum):
    LONG = "long"
    SHORT = "short"

    @property
    def buy_sell(self) -> str:
        return "buy" if self is Side.LONG else "sell"

    def opposite(self) -> "Side":
        return Side.SHORT if self is Side.LONG else Side.LONG


@dataclass(frozen=True)
class Bar:
    symbol: str
    ts_open_ms: int
    ts_close_ms: int
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    closed: bool = True
    source: str = ""

    def validate(self) -> None:
        if not self.closed:
            raise ValueError(f"open/partial bar forbidden: {self.symbol} {self.ts_open_ms}")
        if self.ts_close_ms <= self.ts_open_ms:
            raise ValueError(f"bad bar times: {self.ts_open_ms} {self.ts_close_ms}")
        if self.open <= 0 or self.high <= 0 or self.low <= 0 or self.close <= 0:
            raise ValueError(f"non-positive OHLC: {self}")
        if self.high < max(self.open, self.close) - 1e-12:
            raise ValueError(f"high below open/close: {self}")
        if self.low > min(self.open, self.close) + 1e-12:
            raise ValueError(f"low above open/close: {self}")
        if self.low > self.high:
            raise ValueError(f"low > high: {self}")


@dataclass
class Position:
    symbol: str
    side: Side
    qty: float  # always > 0
    entry: float
    stop: float
    opened_ts_ms: int
    opened_i: int
    notional: float
    entry_fee: float = 0.0
    mark: float = 0.0

    def unrealized(self, price: float | None = None) -> float:
        px = self.mark if price is None else price
        if self.side is Side.LONG:
            return q(self.qty * (px - self.entry))
        return q(self.qty * (self.entry - px))


@dataclass(frozen=True)
class Order:
    """Intent produced by strategy+risk. Filled by the sim, never sent to an exchange."""

    symbol: str
    side: Side
    qty: float
    kind: str  # entry | exit
    reason: str
    stop: float = 0.0
    decision_ts_ms: int = 0
    cloid: str = ""


@dataclass(frozen=True)
class Fill:
    ts_ms: int
    symbol: str
    side: str  # buy | sell
    qty: float
    price: float
    fee: float
    slippage_bps: float
    reason: str
    kind: str
    cloid: str = ""
    pnl: float = 0.0
    ref_price: float = 0.0
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Signal:
    symbol: str
    side: Side
    stop: float
    reason: str
    bar_ts_ms: int
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskDecision:
    allowed: bool
    reason: str
    notional: float = 0.0
    qty: float = 0.0
    leverage: float = 0.0
    risk_budget: float = 0.0
    stop_frac: float = 0.0
