"""Settlement after a flat cycle.

Rules encoded here (brief §4 / §18, as stated for this build):

- Settle only when the cycle is flat (no DOGE position, no scalp position).
- ``W_gross`` is the change in trading NAV T over the cycle, fees included.
  BTC reserve and BTC-pending are outside T, so they do not create ``W_gross``.
- If ``W_gross < 0``, loss carryforward ``L`` increases by ``|W_gross|``.
  No BTC pending is created. Reserve quantity is unchanged.
- If ``W_gross > 0``, the profit repays ``L`` first. While ``L`` remains,
  distributable surplus ``W`` is 0 and BTC pending delta ``B`` is 0.
- After recovery (``L == 0``), surplus ``W = W_gross - recovered`` and
  ``B = 0.60 * W``. ``B`` is moved from trading cash into ``btc_pending_quote``.
  It is not an automatic spot buy and it is not a sell of existing BTC.
- The skim is pro-rata across DOGE and scalp cash. It does not refill a
  sleeve from the other sleeve or from BTC (no downward refill, no average-down).
- Units are redeemed at the pre-skim unit NAV so a distribution is not a
  drawdown. High-water mark is the max unit NAV, not total equity.

Arithmetic examples (also the unit tests):

18.1  A=1000, loss 40 → L=40, B=0, T=360, reserve quote 600, total 960.
18.2  next +25 → recovered 25, L=15, B=0, T=385, total 985.
18.3  next +50 → recovered 15, W=35, B=21, L=0, T=414, pending 21, total 1035.
18.4  fresh A=1000, +100, L=0 → W=100, B=60, T=440, pending 60, total 1100.
      Pre-skim unit NAV 1.25; redeem 48 units; NAV unchanged at 1.25.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from atlas.paper.atlas_cycle.ledger import CapitalLedger
from atlas.paper.atlas_cycle.money import D, ZERO, q


class CycleNotFlat(RuntimeError):
    """Settlement is allowed only after the cycle is flat."""


@dataclass(frozen=True)
class SettlementResult:
    cycle_pnl: Decimal
    loss_carryforward_before: Decimal
    recovered: Decimal
    loss_carryforward_after: Decimal
    distributable_w: Decimal
    btc_pending_delta: Decimal
    doge_skim: Decimal
    scalp_skim: Decimal

    @property
    def fully_recovered(self) -> bool:
        return self.loss_carryforward_after == ZERO


def btc_pending_from_surplus(surplus_w: Decimal) -> Decimal:
    """B = 0.60 * W after loss carryforward is cleared. Else 0."""
    if surplus_w <= 0:
        return ZERO
    return q(surplus_w * D("0.60"))


def settle_flat_cycle(
    ledger: CapitalLedger,
    cycle_open_t: object,
    *,
    flat: bool,
) -> SettlementResult:
    """Apply one flat-cycle settlement. ``cycle_open_t`` is T at cycle open."""
    if not flat:
        raise CycleNotFlat("settlement only after a flat cycle")
    open_t = q(D(cycle_open_t))
    if open_t < 0:
        raise ValueError("cycle open T cannot be negative")
    trading = ledger.trading_nav()
    w_gross = q(trading - open_t)
    l_before = ledger.loss_carryforward
    doge_skim = ZERO
    scalp_skim = ZERO

    if w_gross < 0:
        recovered = ZERO
        ledger.loss_carryforward = q(l_before + (-w_gross))
        surplus = ZERO
        pending_delta = ZERO
    elif w_gross == 0:
        recovered = ZERO
        surplus = ZERO
        pending_delta = ZERO
    else:
        recovered = q(min(w_gross, l_before))
        ledger.loss_carryforward = q(l_before - recovered)
        surplus = q(w_gross - recovered)
        pending_delta = (
            btc_pending_from_surplus(surplus) if ledger.loss_carryforward == ZERO else ZERO
        )

    if pending_delta > 0:
        doge_skim, scalp_skim = _skim_pending(ledger, pending_delta)

    return SettlementResult(
        cycle_pnl=w_gross,
        loss_carryforward_before=l_before,
        recovered=recovered,
        loss_carryforward_after=ledger.loss_carryforward,
        distributable_w=surplus,
        btc_pending_delta=pending_delta,
        doge_skim=doge_skim,
        scalp_skim=scalp_skim,
    )


def _skim_pending(ledger: CapitalLedger, pending_delta: Decimal) -> tuple[Decimal, Decimal]:
    """Move B from T into btc_pending. Redeem units so unit NAV is unchanged."""
    trading = ledger.trading_nav()
    if pending_delta > trading:
        raise ValueError("BTC pending skim exceeds trading NAV")
    if trading == 0:
        raise ValueError("cannot skim an empty trading book")
    nav = ledger.nav_per_unit()
    redeem = pending_delta / nav
    doge_skim = q(pending_delta * ledger.doge_cash / trading)
    scalp_skim = q(pending_delta - doge_skim)
    if doge_skim > ledger.doge_cash or scalp_skim > ledger.scalp_cash:
        raise ValueError("pro-rata skim exceeded a sleeve; refusing reserve use")
    ledger.doge_cash = q(ledger.doge_cash - doge_skim)
    ledger.scalp_cash = q(ledger.scalp_cash - scalp_skim)
    ledger.btc_pending_quote = q(ledger.btc_pending_quote + pending_delta)
    ledger.units = ledger.units - redeem
    if ledger.units <= 0:
        raise ValueError("unit redemption exhausted trading units")
    # Distribution must not lower or raise unit NAV, and must not cut HWM.
    return doge_skim, scalp_skim
