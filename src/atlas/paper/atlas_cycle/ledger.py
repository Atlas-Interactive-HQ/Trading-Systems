"""Capital ledger for Atlas Cycle v1.

Split of deposit A is 60/30/10 (BTC reserve / DOGE sleeve / scalp sleeve).
Trading NAV ``T`` is DOGE cash + scalp cash. BTC reserve and BTC-pending quote
are excluded from ``T`` and from the unitized high-water mark.

The bot has no path that reduces BTC reserve quantity. Losses cannot spend
the reserve or the pending BTC earmark (no BTC as loss collateral).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from atlas.paper.atlas_cycle.money import D, ZERO, q

# Labeled placeholder so reserve quantity is well-defined in paper.
# Not a market price and not a forecast.
BTC_MARK_PLACEHOLDER = D("100000")


class BtcReserveProtected(RuntimeError):
    """BTC reserve cannot be sold or pledged by the bot."""


class InsufficientSleeveCash(RuntimeError):
    """Sleeve cash cannot fund this debit. Reserve is not a backstop."""


@dataclass
class CapitalLedger:
    deposit_a: Decimal
    btc_reserve_quote: Decimal
    btc_reserve_qty: Decimal
    btc_pending_quote: Decimal
    doge_cash: Decimal
    scalp_cash: Decimal
    loss_carryforward: Decimal
    units: Decimal
    hwm_nav: Decimal
    day_start_t: Decimal
    realized_loss_today: Decimal
    utc_day: str = "1970-01-01"

    def __post_init__(self) -> None:
        self.deposit_a = q(self.deposit_a)
        self.btc_reserve_quote = q(self.btc_reserve_quote)
        self.btc_reserve_qty = D(self.btc_reserve_qty)
        self.btc_pending_quote = q(self.btc_pending_quote)
        self.doge_cash = q(self.doge_cash)
        self.scalp_cash = q(self.scalp_cash)
        self.loss_carryforward = q(self.loss_carryforward)
        self.units = D(self.units)
        self.hwm_nav = D(self.hwm_nav)
        self.day_start_t = q(self.day_start_t)
        self.realized_loss_today = q(self.realized_loss_today)
        if self.btc_reserve_qty <= 0:
            raise ValueError("BTC reserve quantity must stay positive")
        if self.units <= 0:
            raise ValueError("trading units must stay positive")

    @classmethod
    def open_deposit(cls, deposit_a: object, *, utc_day: str = "2026-09-24") -> "CapitalLedger":
        """Split A into 60/30/10. T = 0.40 A. Unit NAV starts at 1."""
        amount = q(D(deposit_a))
        if amount <= 0:
            raise ValueError("paper deposit A must be positive")
        btc = q(amount * D("0.60"))
        doge = q(amount * D("0.30"))
        scalp = q(amount - btc - doge)
        if scalp != q(amount * D("0.10")):
            raise ValueError("6:3:1 split did not conserve A")
        trading = q(doge + scalp)
        qty = btc / BTC_MARK_PLACEHOLDER
        return cls(
            deposit_a=amount,
            btc_reserve_quote=btc,
            btc_reserve_qty=qty,
            btc_pending_quote=ZERO,
            doge_cash=doge,
            scalp_cash=scalp,
            loss_carryforward=ZERO,
            units=trading,
            hwm_nav=D("1"),
            day_start_t=trading,
            realized_loss_today=ZERO,
            utc_day=utc_day,
        )

    def trading_nav(self) -> Decimal:
        """T. BTC reserve and BTC pending are excluded."""
        return q(self.doge_cash + self.scalp_cash)

    def nav_per_unit(self) -> Decimal:
        return self.trading_nav() / self.units

    def total_quote(self) -> Decimal:
        return q(self.btc_reserve_quote + self.btc_pending_quote + self.trading_nav())

    def sleeve_cash(self, sleeve: str) -> Decimal:
        if sleeve == "doge":
            return self.doge_cash
        if sleeve == "scalp":
            return self.scalp_cash
        if sleeve == "btc":
            raise BtcReserveProtected("BTC reserve is not a trading sleeve")
        raise ValueError(f"unknown sleeve {sleeve!r}")

    def apply_realized(self, sleeve: str, pnl: object) -> None:
        """Apply realized sleeve PnL.

        Refuses BTC. Refuses a debit that would make sleeve cash negative
        (no silent leverage raise, no reserve pledge).
        """
        amount = q(D(pnl))
        if sleeve == "btc":
            raise BtcReserveProtected("bot cannot debit or credit BTC reserve via PnL")
        cash = self.sleeve_cash(sleeve)
        if cash + amount < 0:
            raise InsufficientSleeveCash(
                f"{sleeve} cash {cash} cannot absorb {amount}; BTC reserve untouched"
            )
        updated = q(cash + amount)
        if sleeve == "doge":
            self.doge_cash = updated
        elif sleeve == "scalp":
            self.scalp_cash = updated
        else:
            raise ValueError(f"unknown sleeve {sleeve!r}")
        if amount < 0:
            self.realized_loss_today = q(self.realized_loss_today + (-amount))
        self.refresh_hwm()

    def debit_fee(self, sleeve: str, fee: object) -> None:
        fee_q = q(D(fee))
        if fee_q < 0:
            raise ValueError("fee must be >= 0")
        if fee_q == 0:
            return
        self.apply_realized(sleeve, -fee_q)

    def refresh_hwm(self) -> None:
        nav = self.nav_per_unit()
        if nav > self.hwm_nav:
            self.hwm_nav = nav

    def rollover_utc_day(self, utc_day: str) -> bool:
        if utc_day == self.utc_day:
            return False
        self.utc_day = utc_day
        self.day_start_t = self.trading_nav()
        self.realized_loss_today = ZERO
        return True

    def reduce_btc_reserve(self, qty: object) -> None:
        """Always refuses. Present so tests can prove the bot cannot sell BTC."""
        raise BtcReserveProtected(
            "LIVE HOLD: bot must not sell, reduce, or pledge BTC reserve "
            f"(requested qty={qty})"
        )

    def move_pending_to_reserve(self, quote_amount: object, btc_qty: object) -> None:
        """Paper conversion of pending quote into more BTC. Never reduces qty.

        v1 settlement does not call this. Buys stay pending until a later
        explicit paper step.
        """
        quote_q = q(D(quote_amount))
        qty = D(btc_qty)
        if quote_q <= 0 or qty <= 0:
            raise ValueError("BTC add must be positive")
        if quote_q > self.btc_pending_quote:
            raise InsufficientSleeveCash("BTC pending cannot cover this add")
        self.btc_pending_quote = q(self.btc_pending_quote - quote_q)
        self.btc_reserve_quote = q(self.btc_reserve_quote + quote_q)
        self.btc_reserve_qty = self.btc_reserve_qty + qty
