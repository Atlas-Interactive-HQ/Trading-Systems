"""Portfolio risk on unitized trading NAV.

T excludes BTC reserve and BTC pending. Drawdown is
``(HWM - nav_per_unit) / HWM``.

- Cycle risk budget: 1% of T in NORMAL.
- Daily halt: realized trading losses today >= 3% of day-start T.
  Distributions into BTC pending are not daily losses.
- REDUCED: unit drawdown >= 5% and < 10%. Cycle risk halves to 0.5%.
- MANUAL_HALT: unit drawdown >= 10%. Latched until a human acknowledge
  AND drawdown is back under 10%. Acknowledge never raises the risk fraction
  above the NORMAL 1% cap.
- Soft PASS is a no-op: it does not clear a halt and does not widen risk
  or leverage.

LIVE is not a risk mode. Leverage ceilings are configuration, not something
this module increases to fit a small account.
"""

from __future__ import annotations

from decimal import Decimal

from atlas.paper.atlas_cycle.enums import RiskMode
from atlas.paper.atlas_cycle.ledger import CapitalLedger
from atlas.paper.atlas_cycle.money import D, ZERO, q


class SoftPassDoesNotArm(RuntimeError):
    """Raised if a caller tries to treat Soft PASS as a risk widening."""


class LeverageCeilingExceeded(RuntimeError):
    """Configured leverage is above the v1 ceiling. Not raised automatically."""


# v1 ceilings. Do not raise these to make a small account look tradable.
DOGE_LEVERAGE_CEILING = D("2")
SCALP_LEVERAGE_CEILING = D("3")
CYCLE_RISK_FRAC = D("0.01")
REDUCED_CYCLE_RISK_FRAC = D("0.005")
DAILY_HALT_FRAC = D("0.03")
DD_REDUCED_FRAC = D("0.05")
DD_MANUAL_HALT_FRAC = D("0.10")


def assert_leverage_ceilings(
    *,
    doge_leverage: object,
    scalp_leverage_max: object,
) -> tuple[Decimal, Decimal]:
    doge = D(doge_leverage)
    scalp = D(scalp_leverage_max)
    if doge <= 0 or scalp <= 0:
        raise LeverageCeilingExceeded("leverage must be positive")
    if doge > DOGE_LEVERAGE_CEILING:
        raise LeverageCeilingExceeded(
            f"DOGE leverage {doge} exceeds isolated ceiling {DOGE_LEVERAGE_CEILING}; "
            "refusing to trade at a higher multiple"
        )
    if scalp > SCALP_LEVERAGE_CEILING:
        raise LeverageCeilingExceeded(
            f"scalp leverage {scalp} exceeds isolated ceiling {SCALP_LEVERAGE_CEILING}"
        )
    return doge, scalp


def unit_drawdown(ledger: CapitalLedger) -> Decimal:
    hwm = ledger.hwm_nav
    if hwm <= 0:
        return D("1")
    nav = ledger.nav_per_unit()
    if nav >= hwm:
        return ZERO
    return (hwm - nav) / hwm


class PortfolioRisk:
    def __init__(self) -> None:
        self.manual_halt_latched = False
        self.doge_leverage = DOGE_LEVERAGE_CEILING
        self.scalp_leverage_max = SCALP_LEVERAGE_CEILING

    def update(self, ledger: CapitalLedger) -> RiskMode:
        dd = unit_drawdown(ledger)
        if dd >= DD_MANUAL_HALT_FRAC:
            self.manual_halt_latched = True
        if self.manual_halt_latched:
            return RiskMode.MANUAL_HALT
        day_start = ledger.day_start_t
        if day_start > 0 and ledger.realized_loss_today >= q(day_start * DAILY_HALT_FRAC):
            return RiskMode.DAILY_HALT
        if dd >= DD_REDUCED_FRAC:
            return RiskMode.REDUCED
        return RiskMode.NORMAL

    def cycle_risk_frac(self, mode: RiskMode) -> Decimal:
        if mode is RiskMode.NORMAL:
            return CYCLE_RISK_FRAC
        if mode is RiskMode.REDUCED:
            return REDUCED_CYCLE_RISK_FRAC
        return ZERO

    def risk_budget(self, ledger: CapitalLedger, mode: RiskMode | None = None) -> Decimal:
        binding = self.update(ledger) if mode is None else mode
        return q(ledger.trading_nav() * self.cycle_risk_frac(binding))

    def acknowledge_manual_halt(self, ledger: CapitalLedger) -> RiskMode:
        """Human ack. Does not widen. Stays latched while drawdown is >= 10%."""
        if unit_drawdown(ledger) >= DD_MANUAL_HALT_FRAC:
            self.manual_halt_latched = True
            return RiskMode.MANUAL_HALT
        self.manual_halt_latched = False
        return self.update(ledger)

    def apply_soft_pass(self, ledger: CapitalLedger) -> RiskMode:
        """Soft PASS ≠ arm and ≠ widen. Returns the same binding mode."""
        if self.doge_leverage > DOGE_LEVERAGE_CEILING:
            raise SoftPassDoesNotArm("soft pass cannot raise DOGE leverage")
        if self.scalp_leverage_max > SCALP_LEVERAGE_CEILING:
            raise SoftPassDoesNotArm("soft pass cannot raise scalp leverage")
        return self.update(ledger)

    def entries_allowed(self, mode: RiskMode) -> bool:
        return mode in (RiskMode.NORMAL, RiskMode.REDUCED)
