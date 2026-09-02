"""Risk gate: daily 5% kill, one position, size from risk (locked L2/L3/L9/L14).

notional = min(risk_budget / stop_frac, leverage_default * equity, hard_cap * equity, liquidity_cap)

Per-trade risk is locked to [1%, 2%] of equity. Fail closed outside that band.
"""

from __future__ import annotations

from atlas.paper.ledger import Ledger
from atlas.paper.types import RiskDecision, Side, q

# Locked L3
RISK_FRAC_MIN = 0.01
RISK_FRAC_MAX = 0.02


class PaperConfigError(ValueError):
    """Invalid paper risk configuration (fail closed)."""


def validate_risk_params(
    *,
    per_trade_risk_frac: float,
    daily_kill_frac: float,
    leverage_default: float,
    leverage_hard_cap: float,
) -> None:
    if not (RISK_FRAC_MIN - 1e-12 <= per_trade_risk_frac <= RISK_FRAC_MAX + 1e-12):
        raise PaperConfigError(
            f"per_trade_risk_frac must be in [{RISK_FRAC_MIN}, {RISK_FRAC_MAX}] (locked L3); "
            f"got {per_trade_risk_frac}"
        )
    if daily_kill_frac <= 0 or daily_kill_frac > 0.5:
        raise PaperConfigError(f"daily_kill_frac out of range: {daily_kill_frac}")
    if leverage_default <= 0 or leverage_hard_cap <= 0:
        raise PaperConfigError("leverage caps must be positive")
    if leverage_default - 1e-12 > leverage_hard_cap:
        raise PaperConfigError("leverage_default exceeds leverage_hard_cap")


def _reject(reason: str) -> RiskDecision:
    return RiskDecision(allowed=False, reason=reason)


def gate_new_entry(ledger: Ledger, *, one_position: bool = True) -> RiskDecision:
    if ledger.killed:
        return _reject("daily_kill")
    if one_position and ledger.has_position:
        return _reject("one_position")
    if ledger.equity <= 0:
        return _reject("non_positive_equity")
    return RiskDecision(allowed=True, reason="ok")


def check_daily_kill(ledger: Ledger, daily_kill_frac: float) -> bool:
    """Trip kill if UTC-day loss >= daily_kill_frac of day-start equity."""
    start = ledger.day_start_equity
    if start <= 0:
        ledger.killed = True
        ledger.kill_reason = ledger.kill_reason or "non_positive_day_start"
        return True
    loss = start - ledger.equity
    threshold = start * daily_kill_frac
    if loss + 1e-12 >= threshold:
        ledger.killed = True
        ledger.kill_reason = ledger.kill_reason or "daily_loss"
        return True
    return ledger.killed


def size_order(
    *,
    equity: float,
    entry: float,
    stop: float,
    side: Side,
    per_trade_risk_frac: float,
    leverage_default: float,
    leverage_hard_cap: float,
    liquidity_cap: float | None = None,
) -> RiskDecision:
    """Risk-budget sizing. Same numbers → same qty/notional."""
    validate_risk_params(
        per_trade_risk_frac=per_trade_risk_frac,
        daily_kill_frac=0.05,
        leverage_default=leverage_default,
        leverage_hard_cap=leverage_hard_cap,
    )
    if equity <= 0 or entry <= 0:
        return _reject("invalid_equity_or_entry")
    if stop <= 0:
        return _reject("invalid_stop")
    if side is Side.LONG and stop >= entry:
        return _reject("stop_not_below_entry")
    if side is Side.SHORT and stop <= entry:
        return _reject("stop_not_above_entry")

    stop_dist = abs(entry - stop)
    stop_frac = stop_dist / entry
    if stop_frac <= 0:
        return _reject("zero_stop_distance")

    risk_budget = q(equity * per_trade_risk_frac)
    raw_notional = risk_budget / stop_frac
    lev_cap = leverage_default * equity
    hard_cap = leverage_hard_cap * equity
    liq = hard_cap if liquidity_cap is None else liquidity_cap
    if liq <= 0:
        return _reject("liquidity_cap")

    notional = min(raw_notional, lev_cap, hard_cap, liq)
    notional = q(notional)
    if notional <= 0:
        return _reject("zero_notional")
    qty = q(notional / entry)
    if qty <= 0:
        return _reject("zero_qty")
    leverage = notional / equity
    if leverage > leverage_hard_cap + 1e-9:
        return _reject("leverage_hard_cap")
    return RiskDecision(
        allowed=True,
        reason="sized",
        notional=notional,
        qty=qty,
        leverage=q(leverage),
        risk_budget=risk_budget,
        stop_frac=q(stop_frac),
    )
