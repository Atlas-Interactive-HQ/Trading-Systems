"""Paper scalp feasibility under a 0.05% of T0 risk budget.

Public minSz / ctVal / last price come from ``public_probe``. They are labeled
assumptions for this table. The instrument registry stays unverified.

Stop distance used here is 0.50% of the probed last price (ASSUMPTION). Fees
are the yaml taker rate. Slippage is the yaml scalp slippage. Funding is
unknown and is not credited.

A row can place one minimum order when that order's stop risk is within the
budget and the margin fits 80% of scalp cash at the locked 3x ceiling.
Live free collateral is a separate verdict and does not change the ceiling.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from atlas.paper.atlas_cycle.config import (
    INSUFFICIENT_CAPITAL_FOR_FULL_SYSTEM,
    AtlasCycleConfig,
    classify_live_capital,
)
from atlas.paper.atlas_cycle.money import D, q
from atlas.paper.atlas_cycle.public_probe import PUBLIC_SWAPS, PublicSwapSnapshot

STOP_FRAC_ASSUMPTION = D("0.005")
CANDIDATE_ORDER = ("SOL", "ETH", "PEPE")


@dataclass(frozen=True)
class SizeRow:
    asset: str
    deposit_a: Decimal
    risk_budget: Decimal
    min_coin: Decimal
    min_risk: Decimal
    can_place: bool
    skip_reason: str
    roundtrip_cost_of_1_5r: Decimal


def roundtrip_frac(cfg: AtlasCycleConfig) -> Decimal:
    fee = cfg.taker_fee_rate
    slip = cfg.scalp_slippage_bps / D("10000")
    return q(D("2") * fee + D("2") * slip)


def cost_of_gross_target(cfg: AtlasCycleConfig, stop_frac: Decimal) -> Decimal:
    """Round-trip cost as a fraction of a gross 1.5R move."""
    if stop_frac <= 0:
        return D("1")
    gross = D("1.5") * stop_frac
    return roundtrip_frac(cfg) / gross


def _size_row(
    cfg: AtlasCycleConfig,
    snap: PublicSwapSnapshot,
    deposit: Decimal,
) -> SizeRow:
    trading = q(deposit * cfg.trading_frac())
    scalp_cash = q(deposit * cfg.scalp_frac)
    budget = q(trading * cfg.scalp_risk_frac)
    stop_dist = snap.last_price * STOP_FRAC_ASSUMPTION
    min_risk = q(snap.min_coin * stop_dist)
    notional = snap.min_coin * snap.last_price
    margin = notional / cfg.scalp_leverage_max
    reserves = roundtrip_frac(cfg) * notional
    cost = cost_of_gross_target(cfg, STOP_FRAC_ASSUMPTION)
    if min_risk <= 0 or stop_dist <= 0:
        reason = "SKIP_QUOTE_QUANTUM"
        ok = False
    elif min_risk > budget:
        reason = "SKIP_MIN_SIZE"
        ok = False
    elif margin + reserves > cfg.margin_cash_frac_max * scalp_cash:
        reason = "SKIP_MIN_SIZE"
        ok = False
    else:
        reason = ""
        ok = True
    return SizeRow(
        asset=snap.asset,
        deposit_a=deposit,
        risk_budget=budget,
        min_coin=snap.min_coin,
        min_risk=min_risk,
        can_place=ok,
        skip_reason=reason,
        roundtrip_cost_of_1_5r=q(cost),
    )


def feasibility_table(cfg: AtlasCycleConfig) -> list[SizeRow]:
    rows: list[SizeRow] = []
    for asset in CANDIDATE_ORDER:
        snap = PUBLIC_SWAPS[asset]
        for deposit in cfg.paper_deposit_sensitivity:
            rows.append(_size_row(cfg, snap, deposit))
    return rows


def paper_size_passes(rows: list[SizeRow], asset: str) -> bool:
    matched = [row for row in rows if row.asset == asset]
    return bool(matched) and all(row.can_place for row in matched)


def live_full_system_label(cfg: AtlasCycleConfig) -> str:
    """Same verdict as Phase 1. Leverage is not raised to change it."""
    labels = {classify_live_capital(cfg, deposit) for deposit in cfg.paper_deposit_sensitivity}
    if INSUFFICIENT_CAPITAL_FOR_FULL_SYSTEM in labels:
        return INSUFFICIENT_CAPITAL_FOR_FULL_SYSTEM
    return "PAPER_SIM_ONLY"
