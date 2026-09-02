"""Paper ledger: cash, one position, equity. UTC day for the kill switch.

Derivative-style accounting (linear/perp-like): opening does not spend notional,
only fees. Realized PnL and fees hit cash. Equity = cash + unrealized.
USDT/USD marks are treated as EUR 1:1 (documented FX assumption).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from atlas.common.time import utc_date_str
from atlas.paper.types import Fill, Position, Side, q


@dataclass
class Ledger:
    cash: float
    day_start_equity: float
    utc_day: str
    position: Position | None = None
    realized_pnl: float = 0.0
    fees_paid: float = 0.0
    killed: bool = False
    kill_reason: str | None = None
    n_fills: int = 0
    peak_equity: float = 0.0
    extra: dict = field(default_factory=dict)

    @classmethod
    def new(cls, equity_eur: float, ts_ms: int) -> "Ledger":
        eq = q(equity_eur)
        if eq <= 0:
            raise ValueError("starting equity must be positive")
        day = utc_date_str(ts_ms)
        return cls(cash=eq, day_start_equity=eq, utc_day=day, peak_equity=eq)

    @property
    def has_position(self) -> bool:
        return self.position is not None

    @property
    def unrealized(self) -> float:
        if self.position is None:
            return 0.0
        return self.position.unrealized()

    @property
    def equity(self) -> float:
        return q(self.cash + self.unrealized)

    def mark(self, price: float) -> None:
        if self.position is not None:
            if price <= 0:
                raise ValueError("mark price must be positive")
            self.position.mark = price
        self.peak_equity = max(self.peak_equity, self.equity)

    def rollover_utc_day(self, ts_ms: int) -> bool:
        """Reset daily kill baseline on UTC date change. Returns True if rolled."""
        day = utc_date_str(ts_ms)
        if day == self.utc_day:
            return False
        self.utc_day = day
        self.day_start_equity = self.equity
        self.killed = False
        self.kill_reason = None
        return True

    def apply_fill(self, fill: Fill, *, stop: float = 0.0, opened_i: int = 0) -> float:
        """Apply a fill. Returns realized PnL of this fill (0 on entry)."""
        self.n_fills += 1
        self.fees_paid = q(self.fees_paid + fill.fee)
        self.cash = q(self.cash - fill.fee)
        pnl = 0.0
        if fill.kind == "entry":
            if self.position is not None:
                raise RuntimeError("ledger apply_fill entry while already in position")
            side = Side.LONG if fill.side == "buy" else Side.SHORT
            notional = q(fill.qty * fill.price)
            self.position = Position(
                symbol=fill.symbol,
                side=side,
                qty=fill.qty,
                entry=fill.price,
                stop=stop,
                opened_ts_ms=fill.ts_ms,
                opened_i=opened_i,
                notional=notional,
                entry_fee=fill.fee,
                mark=fill.price,
            )
        elif fill.kind == "exit":
            if self.position is None:
                raise RuntimeError("ledger apply_fill exit with no position")
            pos = self.position
            if fill.symbol != pos.symbol:
                raise RuntimeError("exit symbol mismatch")
            if pos.side is Side.LONG:
                pnl = q(pos.qty * (fill.price - pos.entry))
            else:
                pnl = q(pos.qty * (pos.entry - fill.price))
            self.cash = q(self.cash + pnl)
            self.realized_pnl = q(self.realized_pnl + pnl)
            self.position = None
        else:
            raise ValueError(f"unknown fill kind {fill.kind!r}")
        self.peak_equity = max(self.peak_equity, self.equity)
        return pnl

    def snapshot(self, ts_ms: int) -> dict:
        pos = self.position
        return {
            "ts_ms": ts_ms,
            "utc_day": self.utc_day,
            "cash": self.cash,
            "equity": self.equity,
            "unrealized": self.unrealized,
            "realized_pnl": self.realized_pnl,
            "fees_paid": self.fees_paid,
            "killed": self.killed,
            "kill_reason": self.kill_reason,
            "day_start_equity": self.day_start_equity,
            "position": None
            if pos is None
            else {
                "symbol": pos.symbol,
                "side": pos.side.value,
                "qty": pos.qty,
                "entry": pos.entry,
                "stop": pos.stop,
                "notional": pos.notional,
                "mark": pos.mark,
                "upl": pos.unrealized(),
            },
        }
